#!/usr/bin/env python3

"""
utils/process.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-03-04"
__status__ = "Prototype/Development/Production"

# Imports.
import hashlib
import time
import logging
import uuid

from pathlib import Path

from PySide6.QtCore import QProcess, QTimer, Signal, Slot

from swiftguard.init import exceptions as exc, models

# Child logger.
LOGGER = logging.getLogger(__name__)

_BINARY_PATH = Path("/usr/sbin/system_profiler")
bus = "AirPort"


# timeout = 15


class Process:
    def __init__(
            self,
            binary_path: Path | str,
            args: list[str] | tuple[str, ...] | None = None,
            stdin: str | None = None,
            timeout: int = -1,
            timeout_msecs: int = -1,
            blocking: bool = True,
            binary_hash: str | None = None,
            terminate_timeout_msecs: int = 1000,
            ) -> None:
        """
        Wrapper for QProcess to handle process execution and control.

        :param binary_path: Path to the binary/program to execute.
        :type binary_path: Path | str
        :param args: Arguments to pass to the binary (optional).
        :type args: list[str] | tuple[str, ...] | None
        :param stdin: Standard input for the process (optional).
        :type stdin: str | None
        :param timeout: Timeout in seconds for the process to finish.
            If given, the process will be terminated after the timeout.
            (-1 = No timeout)
        :type timeout: int
        :param timeout_msecs: Timeout in milliseconds for the process to
            finish. If you set this, do not set the second's timeout.
        :type timeout_msecs: int
        :param blocking: If True, the process will be executed in
            blocking mode. If False, the run method will return
            immediately and the process will be executed in asynchronous
            mode. In non-blocking mode, you can connect to the finished
            signal of the process to get notified when it has finished.
            Important for non-blocking mode: You have to save the
            Process instance (via __init__ or run method) in a variable
            to keep the process alive until it has finished.
        :type blocking: bool
        :param binary_hash: Hash of the binary to check integrity
            (optional).
        :type binary_hash: str | None
        :param terminate_timeout_msecs: Timeout in milliseconds for the
            process to terminate after calling terminate. If the process
            does not terminate in time, it will be killed.
        :type terminate_timeout_msecs: int
        :return: None
        """

        self.proc: QProcess | None = None

        # Instance parameters.
        self.binary_path: Path = Path(binary_path)

        # Ensure all args are strings.
        if args and not all(isinstance(arg, str) for arg in args):
            args = (str(arg) for arg in args)
        self.args: list[str] | tuple[str] | None = args
        self.stdin: str | None = stdin
        self.timeout: int = timeout
        self.timeout_msecs: int = timeout_msecs
        self.blocking: bool = blocking
        self.terminate_timeout: int = terminate_timeout_msecs

        # Only one timeout can be set.
        if timeout != -1 and timeout_msecs != -1:
            raise ValueError("Only one timeout can be set. "
                             "Either seconds or milliseconds."
                             )

        # Given -> Validate -> Run.
        self.binary_hash: str | None = binary_hash

        # State and results of the process.
        self.id: str = str(uuid.uuid4())
        self.running: bool = False
        self.finished: bool = False
        self.error: QProcess.ProcessError | None = None
        self.return_code: int | None = None
        self.stdout: str | None = None
        self.stderr: str | None = None

        # For connecting if in non-blocking mode.
        self.finished_sig: Signal | None = None

        # Validate and construct process instance.
        self._validate_binary()
        self._construct_proc()

        # Timers for non-blocking mode and for killing process if
        # terminate takes too long.
        self._timeout_timer: QTimer | None = None
        self._terminate_timer: QTimer | None = None
        self._timeout_nonblock_occurred: bool = False

        self._start_time = None
        self._duration: float = 0.0

    def __hash__(self) -> int:

        return hash(
                (self.id, self.binary_path, self.args, self.timeout,
                 self.timeout_msecs, self.blocking, self.binary_hash,
                 self.terminate_timeout)
                )

    def __eq__(self, other: Process) -> bool:
        if not isinstance(other, Process):
            return NotImplemented

        return all(
                getattr(self, attr) == getattr(other, attr)
                for attr in ("id", "binary_path", "args", "timeout",
                             "timeout_msecs", "blocking", "binary_hash",
                             "terminate_timeout")
                )

    def __repr__(self) -> str:
        res = []
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue

            # Truncate long outputs.
            if (k in ("stdout", "stderr", "stdin")
                    and v is not None
                    and len(v) > 20):
                res.append(f"{k}='{v[:20]}'")
                continue

            elif k.endswith("_sig"):
                # res.append(f"{k}=QSignal(...)")
                continue

            elif k == "proc":
                res.append(f"{k}=QProcess(...)")
                continue

            else:
                res.append(f"{k}={v!r}")

        return (f"{self.__class__.__name__}({', '.join(res)}, "
                f"duration={self.duration:.2f})")

    @property
    def duration(self) -> float:
        return self._duration

    def _validate_binary(self) -> None:
        if (not self.binary_path.exists()
                or not self.binary_path.is_file()
                or not self.binary_path.is_absolute()
                or self.binary_path.is_symlink()):
            raise exc.BinaryIntegrityError(
                    f"Binary path '{self.binary_path}' is invalid."
                    )

        # If hash is given, check it.
        if self.binary_hash:

            # Needed if swiftGuard is not yet initialized.
            try:
                from swiftguard.constants import C
                pepper = C.sec.PEPPER
            except Exception:
                pepper = b"swiftGuard-2024"

            f_hash = hashlib.blake2b(person=pepper)
            with open(self.binary_path, "rb") as f:
                while chunk := f.read(8192):
                    f_hash.update(chunk)

            if f_hash.hexdigest() != self.binary_hash:
                raise exc.BinaryIntegrityError(
                        f"Binary '{self.binary_path}' hash mismatch."
                        )

    def _construct_proc(self):
        self.proc = QProcess()

        self.proc.setProgram(str(self.binary_path))
        if self.args:
            self.proc.setArguments(self.args)

        # Set the process input mode based for reading stdin.
        if self.stdin:
            self.proc.setInputChannelMode(
                    QProcess.InputChannelMode.ManagedInputChannel
                    )

        self.proc.finished.connect(self._handle_finished)
        self.proc.stateChanged.connect(self._handle_state)

        # Pass the finished signal of process to instance signal for
        # connecting from outside if in non-blocking mode.
        self.finished_sig = self.proc.finished

    @Slot()
    def _handle_finished(self):

        # print("_handle_finished called")

        self.finished = True
        self.running = False
        self._handle_stdouterr()
        self._handle_exit_code()
        self._handle_error()

        if self._timeout_timer:
            self._timeout_timer.stop()
            self._timeout_timer = None

        if self._terminate_timer:
            self._terminate_timer.stop()
            self._terminate_timer = None

        # Calculate duration.
        self._duration = time.perf_counter() - self._start_time

    def _handle_stdouterr(self) -> None:
        self.stdout = self.proc.readAllStandardOutput().data().decode("utf-8")
        self.stderr = self.proc.readAllStandardError().data().decode("utf-8")

    def _handle_exit_code(self):

        # QProcess finished normally -> Get exit code.
        if self.proc.exitStatus() == QProcess.ExitStatus.NormalExit:
            self.return_code = self.proc.exitCode()

        # We could not finish the process -> Set exit code to 1.
        else:
            # print("exitStatus:", self.proc.exitStatus())
            self.return_code = 1

    def _handle_error(self):
        err = self.proc.error()
        # print("NONBLOCK TIMEOUT:", self._timeout_nonblock_occurred)

        # Success -> self.error = None. UnknownError -> Default value.
        if err == QProcess.ProcessError.UnknownError:
            self.error = None

        # print("REMAIN:", self._timeout_timer.remainingTime())

        # Process timed out (if we terminate it, we get Crashed).
        elif self.timeout != -1 or self.timeout_msecs != -1:
            # if (self._timeout_nonblock_occurred
            #         or (err == QProcess.ProcessError.Crashed
            #             and self._timeout_timer is not None
            #             and not self._timeout_timer.isActive())
            #         or err == QProcess.ProcessError.Timedout):
            #     self.return_code = 2
            #     self.error = QProcess.ProcessError.Timedout
            #     self.stderr = ""
            #     self.stdout = ""
            #     self._timeout_nonblock_occurred = False  # Reset.

            if self._timeout_nonblock_occurred:
                self.return_code = 2
                self.error = QProcess.ProcessError.Timedout
                self.stderr = ""
                self.stdout = ""
                self._timeout_nonblock_occurred = False  # Reset.

        else:
            self.error = err

            # print("err:", err)

    def __del__(self):

        # Prevent deletion of background process before it has finished.
        if (not self.finished) and (not self.blocking):
            self.proc.waitForFinished(30000)
            self.proc.terminate()

    @Slot()
    def _handle_state(self, state: QProcess.ProcessState) -> None:

        # print("_handle_state called:", state)

        if state == QProcess.ProcessState.NotRunning:
            self.running = False
        else:
            self.running = True

    def _handle_timeout(self):
        self._timeout_nonblock_occurred = True

    def run(self) -> Process:

        if self.running:
            LOGGER.warning(
                    f"Process (ID: {self.id!r}) is already running. Did not "
                    f"start."
                    )
            return self

        if self.timeout != -1:
            timeout_for_proc = self.timeout * 1000
        else:
            timeout_for_proc = self.timeout_msecs

        self._start_time = time.perf_counter()

        if self.blocking:
            self.proc.start()

            # Read stdin.
            if self.stdin:
                self.proc.write(self.stdin.encode("utf-8"))
                self.proc.closeWriteChannel()

            if not self.proc.waitForFinished(msecs=timeout_for_proc):
                self._timeout_nonblock_occurred = True
                self.proc.terminate()
                if not self.proc.waitForFinished(250):
                    self.proc.kill()
        else:
            # print("non blocking called")

            self.proc.start()

            # Read stdin.
            if self.stdin:
                self.proc.write(self.stdin.encode("utf-8"))
                self.proc.closeWriteChannel()

            # Timeout set.
            if timeout_for_proc != -1:
                if timeout_for_proc == 0:
                    timeout_for_proc = 1

                self._timeout_timer = QTimer()
                self._timeout_timer.setSingleShot(True)
                self._timeout_timer.timeout.connect(self.terminate)
                self._timeout_timer.timeout.connect(self._handle_timeout)
                self._timeout_timer.start(timeout_for_proc)

        # print("RET:", self.return_code)

        return self

    def terminate(self):
        # print("terminate called")

        # Process is not running.
        if (not self.proc) or (not self.running):
            return

        # print("terminating now")
        self.proc.terminate()

        # If terminate does not work, kill the process.
        self._terminate_timer = QTimer()
        self._terminate_timer.setSingleShot(True)
        self._terminate_timer.timeout.connect(self.kill)
        self._terminate_timer.start(self.terminate_timeout)

    def kill(self):
        # print("kill called")

        # Process is not running or already finished.
        if (not self.proc
                or not self.running
                or self.finished):
            # print("already killed")
            return

        # if self._timeout_timer:
        #     self._timeout_timer.stop()
        #     self._timeout_timer = None
        #
        # if self._terminate_timer:
        #     self._terminate_timer.stop()
        #     self._terminate_timer = None

        self.proc.kill()
        # print("proc.kill() called")


# class ProcessManager(metaclass=models.Singleton):
#     """
#     Managing for all created ProcessWrapper instances.
#
#     :ivar processes: Dict to store created ProcessWrapper instances.
#     :type processes: dict[str, Process]
#     """
#
#     def __init__(self) -> None:
#         """
#         We store all created Process instances in a WeakSet to
#         prevent circular references and memory leaks. When we close the
#         application, we can ensure all processes are terminated.
#
#         :return: None
#         """
#
#         super().__init__()
#         self.processes = {}
#
#
#     def cleanup_non_running(self) -> None:
#         """
#         Cleanup all non-running processes.
#
#         :return: None
#         """
#
#         for name, proc in self.processes.items():
#             if not proc.running:
#                 self.processes.pop(name)
#
#     def get(
#             self,
#             name: str,
#             ) -> Process:
#
#         proc = self.processes.get(name, None)
#
#         if not proc:
#             raise ValueError(f"Process with name {name!r} not found.")
#
#         return proc
#
#     def __repr__(self) -> str:
#         """
#         Return a string representation of the ProcessManager instance.
#         Only lists the id, binary_path and args of the processes.
#
#         :return: String representation of the ProcessManager instance.
#         :rtype: str
#         """
#
#         procs_repr = [(f"Process("
#                        f"name='{name}', "
#                        f"id={proc.id!r}, "
#                        f"binary_path='{proc.binary_path}', "
#                        f"args={proc.args!r}, "
#                        f"running={proc.running})") for name, proc in
#                       self.processes.items()]
#
#         return (f"{self.__class__.__qualname__}("
#                 f"processes=[{', '.join(procs_repr)}])")
#
#     @property
#     def processes_running(self) -> bool:
#         """
#         Check if any process is currently running.
#
#         :return: True if any process is running, False otherwise.
#         :rtype: bool
#         """
#
#         return any(proc.running for proc in self.processes.values())
#
#     @property
#     def processes_running_list(self) -> list[Process]:
#         """
#         Return a list of all running processes.
#
#         :return: List of all running processes.
#         :rtype: list[Process]
#         """
#         return [proc for proc in self.processes.values() if proc.running]
#
#     def process_by_id(self, process_id: str) -> Process | None:
#         """
#         Return a ProcessWrapper by its id, if it exists.
#
#         :param process_id: The id of the process to return.
#         :type process_id: str
#         :return: The process with the given id or None.
#         :rtype: Process | None
#         """
#
#         for proc in self.processes.values():
#             if proc.id == process_id:
#                 return proc
#
#     def add(self, name: str, process: Process) -> None:
#         """
#         Add a ProcessWrapper instance to the manager.
#
#         :param name: Name to add the ProcessWrapper under as dict key.
#         :type name: str
#         :param process: The ProcessWrapper instance to add.
#         :type process: Process
#         :return: None
#         """
#
#         if name in self.processes:
#             raise ValueError(f"Process with name {name!r} already exists.")
#
#         self.processes[name] = process
#
#     def remove(self, process: Process) -> None:
#         """
#         Remove a ProcessWrapper instance from the manager.
#
#         :param process: The ProcessWrapper instance to remove.
#         :type process: Process
#         :return: None
#         """
#
#         for name, proc in self.processes.items():
#             if proc == process:
#                 self.processes.pop(name)
#                 return
#
#         raise ValueError("Process not found in ProcessManager.")
#
#     def remove_by_name(self, name: str) -> None:
#         """
#         Remove a Process instance by its dict key from manager.
#
#         :param name: Name of the Process to remove.
#         :type name: str
#         :return: None
#         """
#
#         if name not in self.processes:
#             raise ValueError("Process not found in ProcessManager.")
#
#         self.processes.pop(name)
#
#     def terminate_by_name(self, name: str) -> None:
#         """
#         Terminate a process by its id (soft-exit).
#
#         :param name: The name of the Process to terminate.
#         :type name: str
#         :return: None
#         """
#
#         proc = self.processes.get(name, None)
#         if proc:
#             proc.terminate()
#             return
#
#         raise ValueError("Process not found in ProcessManager.")
#
#     def kill_by_name(self, name: str) -> None:
#         """
#         Kill a process by its id (hard-exit).
#
#         :param name: The name of the Process to kill.
#         :type name: str
#         :return: None
#         """
#
#         proc = self.processes.get(name, None)
#         if proc:
#             proc.kill()
#             return
#
#         raise ValueError("Process not found in ProcessManager.")
#
#     def terminate_all(self) -> None:
#         """
#         Terminate all running processes (soft-exit).
#
#         :return: None
#         """
#         for proc in self.processes.values():
#             if proc.running:
#                 proc.terminate()
#
#     def kill_all(self) -> None:
#         """
#         Kill all running processes (hard-exit).
#
#         :return: None
#         """
#
#         for proc in self.processes.values():
#             if proc.running:
#                 proc.kill()


from PySide6.QtWidgets import (QApplication, QPushButton, QVBoxLayout,
                               QWidget)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.bin = _BINARY_PATH
        self.bi2n = Path("/bin/sleep")
        self.args = ("SPAirPortDataType", "-xml", "-detailLevel", "full")
        self.args2 = ("5",)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.btn_start_blocking = QPushButton("Start Blocking")
        self.btn_start_blocking.clicked.connect(self.start_blocking)
        layout.addWidget(self.btn_start_blocking)

        self.btn_start_non_blocking = QPushButton("Start Non-Blocking")
        self.btn_start_non_blocking.clicked.connect(self.start_non_blocking)
        layout.addWidget(self.btn_start_non_blocking)

        self.btn_run_once = QPushButton("Run")
        self.btn_run_once.clicked.connect(self.run)
        layout.addWidget(self.btn_run_once)

        self.btn_terminate = QPushButton("Terminate")
        self.btn_terminate.clicked.connect(self.terminate_process)
        layout.addWidget(self.btn_terminate)

        self.btn_kill = QPushButton("Kill")
        self.btn_kill.clicked.connect(self.kill_process)
        layout.addWidget(self.btn_kill)

        self.bnt_cleanup = QPushButton("Cleanup")
        self.bnt_cleanup.clicked.connect(self.cleanup)
        layout.addWidget(self.bnt_cleanup)

        self.btn_show = QPushButton("Show")
        self.btn_show.clicked.connect(self.show_state)
        layout.addWidget(self.btn_show)

        self.setLayout(layout)
        self.setWindowTitle("Process Control")
        self.show()

    def start_blocking(self):
        # self.process_wrapper_block = Process(
        #         self.bin, self.args,
        #         timeout=10, )
        # self.process_wrapper_block.run()
        #
        # print("blocking done")
        # app = QApplication.instance()
        # print(app.process_mgr)

        Process(
                binary_path="/usr/bin/afplay",
                args=("/System/Library/Sounds/Submarine.aiff",),
                timeout_msecs=700,
                blocking=True,
                ).run()

        print("DONE BLOCK")

    def start_non_blocking(self):
        self.process_wrapper_noblock = Process(
                binary_path="/usr/bin/afplay",
                args=("/System/Library/Sounds/Submarine.aiff",),
                timeout_msecs=700,
                blocking=False
                )
        self.process_wrapper_noblock.run()

    def run(self):
        ...
        # proc = ProcessManager.instance.run(
        #         binary_path=self.bin,
        #         args=self.args,
        #         timeout=5,
        #         blocking=False
        #         )

        print("run_once done")
        #
        # while proc.running:
        #     print("While warten:", proc.running)
        #     print("While procmng:", ProcessManager.instance)
        #     time.sleep(3)

        print("while done")

    def terminate_process(self):
        self.process_wrapper.terminate()

    def kill_process(self):
        self.process_wrapper.kill()

    def cleanup(self):
        ins = models.Singleton.all_instances()

        print(ins, type(ins))
        print("SINGLETON:", ins["ProcessManager"])

    def show_state(self):
        print("RET", self.process_wrapper_noblock.return_code)

        return
        app = QApplication.instance()
        print(app.process_mgr)
        print(len(app.process_mgr.processes))
        print(app.process_mgr.processes_running)


if __name__ == "__main__":
    import sys

    app = QApplication()
    window = MainWindow()
    sys.exit(app.exec())
