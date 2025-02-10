# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'window_uiGvGHkf.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI
# file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QMainWindow, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)
from swiftguard.assets import resources_rc


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(320, 461)
        MainWindow.setMinimumSize(QSize(320, 0))
        MainWindow.setMaximumSize(QSize(320, 800))
        MainWindow.setStyleSheet(
                u"/* ########## Hide all frame borders ########## */\n"
                "QFrame{\n"
                "        border: 0px;\n"
                "        border-style: none;\n"
                "}\n"
                "\n"
                "#centralwidget{\n"
                "		background-color: rgb(253, 253, 255);\n"
                "        border-radius: 16px;\n"
                "		border-width: 1.5px;\n"
                "		border-color: rgb(232, 234, 239);\n"
                "		border-style: outset;\n"
                "\n"
                "        background-image: url(':/icns/light/bg.png');\n"
                "        background-repeat: no-repeat;\n"
                "        background-position: right bottom;\n"
                "\n"
                "}\n"
                "\n"
                "\n"
                "#usb_left QPushButton{\n"
                "		background-color: transparent;\n"
                "		color: rgb(252, 252, 252);\n"
                "		text-align:left;\n"
                "		letter-spacing: 1.8px;\n"
                "		font-weight: 700;\n"
                "}\n"
                "\n"
                "\n"
                "#usb_allowed{\n"
                "		background-color: transparent;\n"
                "		color: rgb(252, 252, 252);\n"
                "		text-align:left;\n"
                "		letter-spacing: 0.7px;\n"
                "		font-weight: 600;\n"
                "         border: none;\n"
                "}\n"
                "\n"
                "\n"
                "\n"
                "/*\n"
                "#usb_count{\n"
                "    background-color: rgb(239, 147, 157);\n"
                "    color: rgb(252, 252, 252);\n"
                "    font-weight: 600"
                ";\n"
                "    text-align:center;\n"
                "    border-radius: 9.4px;\n"
                "}\n"
                "*/\n"
                "\n"
                "\n"
                "#usb_dropdown{\n"
                "		background-color: rgb(247, 246, 251);\n"
                "		border-bottom-left-radius: 16px;\n"
                "		border-bottom-right-radius: 16px;\n"
                "		border-color: rgb(232, 234, 239);\n"
                "		border-width: 1.5px;\n"
                "		border-style: inset;\n"
                "}\n"
                "\n"
                "#usb_dropdown QPushButton{\n"
                "		background-color: transparent;\n"
                "		color: rgb(164, 165, 172);\n"
                "		letter-spacing: 0.8px;\n"
                "		font-weight: 700;\n"
                "         border: none;\n"
                "         text-align: left;\n"
                "         max-width: 212px;\n"
                "         white-space: nowrap;\n"
                "}\n"
                "\n"
                "#usb_dropdown QPushButton:hover{\n"
                "		color: rgb(118, 118, 118);\n"
                "}\n"
                "\n"
                "#usb_dropdown QPushButton:checked{\n"
                "		color: rgb(68, 68, 68);\n"
                "}\n"
                "\n"
                "#usb_dropdown QPushButton:checked:hover{\n"
                "		color: rgb(0, 0, 0);\n"
                "}\n"
                "\n"
                "\n"
                "#ctrl_frame QPushButton{\n"
                "		background-color: transparent;\n"
                "}\n"
                "\n"
                "/** NEEW **/\n"
                "\n"
                "#counter_left QPushButton,#countdown_left QPushButton{\n"
                ""
                "		background-color: transparent;\n"
                "		color: rgb(52, 52, 52);\n"
                "		text-align:left;\n"
                "		font-weight: 600;\n"
                "}\n"
                "\n"
                "#counter_button,#countdown_button{\n"
                "         background: rgb(237, 236, 241);\n"
                "         border-radius: 9px;\n"
                "}\n"
                "\n"
                "#counter_icon,#countdown_text{\n"
                "    color: rgb(52, 52, 52);\n"
                "    font-weight: 600;\n"
                "    text-align:center;\n"
                "    border: none;\n"
                "}\n"
                "\n"
                ""
                )
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
                self.centralwidget.sizePolicy().hasHeightForWidth()
                )
        self.centralwidget.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget = QWidget(self.centralwidget)
        self.widget.setObjectName(u"widget")
        sizePolicy.setHeightForWidth(
                self.widget.sizePolicy().hasHeightForWidth()
                )
        self.widget.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(self.widget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(6, 6, 6, 2)
        self.usb = QFrame(self.widget)
        self.usb.setObjectName(u"usb")
        self.usb.setMinimumSize(QSize(0, 0))
        font = QFont()
        font.setBold(True)
        font.setItalic(False)
        self.usb.setFont(font)
        self.usb.setFrameShape(QFrame.StyledPanel)
        self.usb.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.usb)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.usb_dropdown = QFrame(self.usb)
        self.usb_dropdown.setObjectName(u"usb_dropdown")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
                self.usb_dropdown.sizePolicy().hasHeightForWidth()
                )
        self.usb_dropdown.setSizePolicy(sizePolicy1)
        self.usb_dropdown.setMinimumSize(QSize(260, 0))
        self.usb_dropdown.setMaximumSize(QSize(260, 16777215))
        self.usb_dropdown.setFrameShape(QFrame.StyledPanel)
        self.usb_dropdown.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.usb_dropdown)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(24, 10, 24, 14)
        self.usb_placeholder = QPushButton(self.usb_dropdown)
        self.usb_placeholder.setObjectName(u"usb_placeholder")
        self.usb_placeholder.setEnabled(False)
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
                self.usb_placeholder.sizePolicy().hasHeightForWidth()
                )
        self.usb_placeholder.setSizePolicy(sizePolicy2)
        self.usb_placeholder.setMinimumSize(QSize(0, 27))
        self.usb_placeholder.setMaximumSize(QSize(212, 27))
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        self.usb_placeholder.setFont(font1)
        self.usb_placeholder.setCursor(QCursor(Qt.PointingHandCursor))
        self.usb_placeholder.setIconSize(QSize(9, 9))
        self.usb_placeholder.setCheckable(False)

        self.verticalLayout.addWidget(self.usb_placeholder)

        self.gridLayout.addWidget(self.usb_dropdown, 1, 0, 1, 1,
                                  Qt.AlignHCenter | Qt.AlignTop
                                  )

        self.usb_button = QWidget(self.usb)
        self.usb_button.setObjectName(u"usb_button")
        self.usb_button.setMinimumSize(QSize(283, 40))
        self.usb_button.setMaximumSize(QSize(16777215, 40))
        self.usb_button.setStyleSheet(u"#usb_button{\n"
                                      "         background: qlineargradient("
                                      "spread:pad, x1:0, y1:0, x2:1, y2:0, "
                                      "stop:0 rgb(237, 127, 137), stop:1 "
                                      "rgb(255, 167, 167));\n"
                                      "         border-radius: 11px;\n"
                                      "}\n"
                                      "\n"
                                      "#usb_button:hover{\n"
                                      "    background: qlineargradient("
                                      "spread:pad, x1:0, y1:0, x2:1, y2:0, "
                                      "stop:0 rgb(255, 147, 157), stop:1 "
                                      "rgb(255, 187, 187));\n"
                                      "}"
                                      )
        self.horizontalLayout_3 = QHBoxLayout(self.usb_button)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.usb_left = QFrame(self.usb_button)
        self.usb_left.setObjectName(u"usb_left")
        self.usb_left.setMinimumSize(QSize(121, 0))
        self.usb_left.setFrameShape(QFrame.StyledPanel)
        self.usb_left.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.usb_left)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(18, 0, 0, 0)
        self.usb_state = QPushButton(self.usb_left)
        self.usb_state.setObjectName(u"usb_state")
        self.usb_state.setMaximumSize(QSize(115, 30))
        font2 = QFont()
        font2.setPointSize(16)
        font2.setBold(True)
        self.usb_state.setFont(font2)
        self.usb_state.setCursor(QCursor(Qt.PointingHandCursor))
        icon = QIcon()
        icon.addFile(u":/icns/cable.connector.svg", QSize(), QIcon.Normal,
                     QIcon.Off
                     )
        self.usb_state.setIcon(icon)
        self.usb_state.setIconSize(QSize(24, 24))
        self.usb_state.setCheckable(True)
        self.usb_state.setChecked(True)

        self.horizontalLayout.addWidget(self.usb_state, 0, Qt.AlignLeft)

        self.horizontalLayout_3.addWidget(self.usb_left)

        self.usb_right = QFrame(self.usb_button)
        self.usb_right.setObjectName(u"usb_right")
        sizePolicy.setHeightForWidth(
                self.usb_right.sizePolicy().hasHeightForWidth()
                )
        self.usb_right.setSizePolicy(sizePolicy)
        self.usb_right.setLayoutDirection(Qt.LeftToRight)
        self.usb_right.setFrameShape(QFrame.StyledPanel)
        self.usb_right.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.usb_right)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(15, 0, 20, 0)
        self.usb_count = QPushButton(self.usb_right)
        self.usb_count.setObjectName(u"usb_count")
        sizePolicy2.setHeightForWidth(
                self.usb_count.sizePolicy().hasHeightForWidth()
                )
        self.usb_count.setSizePolicy(sizePolicy2)
        self.usb_count.setMinimumSize(QSize(20, 20))
        self.usb_count.setMaximumSize(QSize(20, 20))
        font3 = QFont()
        font3.setPointSize(11)
        font3.setBold(True)
        self.usb_count.setFont(font3)
        self.usb_count.setLayoutDirection(Qt.RightToLeft)
        self.usb_count.setStyleSheet(u"#usb_count{\n"
                                     "    background-color: rgb(229, 137, "
                                     "147);\n"
                                     "    color: rgb(252, 252, 252);\n"
                                     "    font-weight: 600;\n"
                                     "    text-align:center;\n"
                                     "    border-radius: 10.4px;\n"
                                     "}\n"
                                     ""
                                     )
        self.usb_count.setCheckable(False)

        self.horizontalLayout_2.addWidget(self.usb_count)

        self.usb_allowed = QPushButton(self.usb_right)
        self.usb_allowed.setObjectName(u"usb_allowed")
        self.usb_allowed.setEnabled(True)
        sizePolicy2.setHeightForWidth(
                self.usb_allowed.sizePolicy().hasHeightForWidth()
                )
        self.usb_allowed.setSizePolicy(sizePolicy2)
        self.usb_allowed.setMinimumSize(QSize(64, 15))
        self.usb_allowed.setMaximumSize(QSize(64, 30))
        self.usb_allowed.setFont(font1)
        self.usb_allowed.setCursor(QCursor(Qt.PointingHandCursor))
        self.usb_allowed.setLayoutDirection(Qt.RightToLeft)
        icon1 = QIcon()
        icon1.addFile(u":/icns/chevron.down.svg", QSize(), QIcon.Normal,
                      QIcon.Off
                      )
        icon1.addFile(u":/icns/chevron.up.svg", QSize(), QIcon.Normal,
                      QIcon.On
                      )
        icon1.addFile(u":/icns/chevron.down.svg", QSize(), QIcon.Disabled,
                      QIcon.Off
                      )
        icon1.addFile(u":/icns/chevron.up.svg", QSize(), QIcon.Disabled,
                      QIcon.On
                      )
        self.usb_allowed.setIcon(icon1)
        self.usb_allowed.setIconSize(QSize(12, 12))
        self.usb_allowed.setCheckable(True)
        self.usb_allowed.setChecked(True)

        self.horizontalLayout_2.addWidget(self.usb_allowed)

        self.horizontalLayout_3.addWidget(self.usb_right)

        self.gridLayout.addWidget(self.usb_button, 0, 0, 1, 1)

        self.verticalLayout_3.addWidget(self.usb, 0, Qt.AlignTop)

        self.prefs = QFrame(self.widget)
        self.prefs.setObjectName(u"prefs")
        self.prefs.setMinimumSize(QSize(0, 0))
        self.prefs.setMaximumSize(QSize(16777215, 16777215))
        self.prefs.setFrameShape(QFrame.StyledPanel)
        self.prefs.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.prefs)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setVerticalSpacing(0)
        self.gridLayout_2.setContentsMargins(0, 8, 0, 0)
        self.counter_measure = QFrame(self.prefs)
        self.counter_measure.setObjectName(u"counter_measure")
        self.counter_measure.setMinimumSize(QSize(0, 0))
        self.counter_measure.setMaximumSize(QSize(16777215, 150))
        self.counter_measure.setFrameShape(QFrame.StyledPanel)
        self.counter_measure.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.counter_measure)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 6, 0, 6)
        self.counter_button = QWidget(self.counter_measure)
        self.counter_button.setObjectName(u"counter_button")
        self.counter_button.setMinimumSize(QSize(283, 30))
        self.counter_button.setMaximumSize(QSize(16777215, 30))
        self.counter_button.setStyleSheet(u"")
        self.horizontalLayout_7 = QHBoxLayout(self.counter_button)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.counter_left = QFrame(self.counter_button)
        self.counter_left.setObjectName(u"counter_left")
        self.counter_left.setMinimumSize(QSize(121, 0))
        self.counter_left.setFrameShape(QFrame.StyledPanel)
        self.counter_left.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.counter_left)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(18, 0, 0, 0)
        self.counter_left_button = QPushButton(self.counter_left)
        self.counter_left_button.setObjectName(u"counter_left_button")
        self.counter_left_button.setMinimumSize(QSize(130, 0))
        self.counter_left_button.setMaximumSize(QSize(130, 30))
        font4 = QFont()
        font4.setPointSize(12)
        font4.setBold(True)
        self.counter_left_button.setFont(font4)
        self.counter_left_button.setIconSize(QSize(24, 24))
        self.counter_left_button.setCheckable(False)
        self.counter_left_button.setChecked(False)

        self.horizontalLayout_8.addWidget(self.counter_left_button, 0,
                                          Qt.AlignLeft
                                          )

        self.horizontalLayout_7.addWidget(self.counter_left)

        self.counter_right = QFrame(self.counter_button)
        self.counter_right.setObjectName(u"counter_right")
        sizePolicy.setHeightForWidth(
                self.counter_right.sizePolicy().hasHeightForWidth()
                )
        self.counter_right.setSizePolicy(sizePolicy)
        self.counter_right.setLayoutDirection(Qt.LeftToRight)
        self.counter_right.setFrameShape(QFrame.StyledPanel)
        self.counter_right.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.counter_right)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(15, 0, 0, 0)
        self.counter_icon = QPushButton(self.counter_right)
        self.counter_icon.setObjectName(u"counter_icon")
        sizePolicy2.setHeightForWidth(
                self.counter_icon.sizePolicy().hasHeightForWidth()
                )
        self.counter_icon.setSizePolicy(sizePolicy2)
        self.counter_icon.setMinimumSize(QSize(60, 30))
        self.counter_icon.setMaximumSize(QSize(60, 30))
        self.counter_icon.setFont(font3)
        self.counter_icon.setLayoutDirection(Qt.RightToLeft)
        self.counter_icon.setStyleSheet(u"#usb_count{\n"
                                        "    background-color: rgb(229, 137, "
                                        "147);\n"
                                        "    color: rgb(252, 252, 252);\n"
                                        "    font-weight: 600;\n"
                                        "    text-align:center;\n"
                                        "    border-radius: 9.4px;\n"
                                        "}\n"
                                        ""
                                        )
        icon2 = QIcon()
        icon2.addFile(u":/icns/light/powersleep.svg", QSize(), QIcon.Normal,
                      QIcon.Off
                      )
        icon2.addFile(u":/icns/light/powersleep.svg", QSize(), QIcon.Disabled,
                      QIcon.Off
                      )
        icon2.addFile(u":/icns/light/powersleep.svg", QSize(), QIcon.Selected,
                      QIcon.Off
                      )
        self.counter_icon.setIcon(icon2)
        self.counter_icon.setIconSize(QSize(14, 14))
        self.counter_icon.setCheckable(False)

        self.horizontalLayout_9.addWidget(self.counter_icon, 0, Qt.AlignRight)

        self.horizontalLayout_7.addWidget(self.counter_right, 0,
                                          Qt.AlignRight | Qt.AlignVCenter
                                          )

        self.verticalLayout_5.addWidget(self.counter_button)

        self.gridLayout_2.addWidget(self.counter_measure, 0, 0, 1, 1,
                                    Qt.AlignBottom
                                    )

        self.countdown = QFrame(self.prefs)
        self.countdown.setObjectName(u"countdown")
        self.countdown.setMinimumSize(QSize(0, 0))
        self.countdown.setMaximumSize(QSize(16777215, 280))
        self.countdown.setFrameShape(QFrame.StyledPanel)
        self.countdown.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.countdown)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 6, 0, 6)
        self.countdown_button = QWidget(self.countdown)
        self.countdown_button.setObjectName(u"countdown_button")
        self.countdown_button.setMinimumSize(QSize(283, 30))
        self.countdown_button.setMaximumSize(QSize(16777215, 30))
        self.countdown_button.setStyleSheet(u"")
        self.horizontalLayout_10 = QHBoxLayout(self.countdown_button)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.countdown_left = QFrame(self.countdown_button)
        self.countdown_left.setObjectName(u"countdown_left")
        self.countdown_left.setMinimumSize(QSize(121, 0))
        self.countdown_left.setFrameShape(QFrame.StyledPanel)
        self.countdown_left.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.countdown_left)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(18, 0, 0, 0)
        self.countdown_left_button = QPushButton(self.countdown_left)
        self.countdown_left_button.setObjectName(u"countdown_left_button")
        self.countdown_left_button.setMinimumSize(QSize(130, 0))
        self.countdown_left_button.setMaximumSize(QSize(130, 30))
        self.countdown_left_button.setFont(font4)
        self.countdown_left_button.setIconSize(QSize(24, 24))
        self.countdown_left_button.setCheckable(False)
        self.countdown_left_button.setChecked(False)

        self.horizontalLayout_11.addWidget(self.countdown_left_button, 0,
                                           Qt.AlignLeft
                                           )

        self.horizontalLayout_10.addWidget(self.countdown_left)

        self.countdown_right = QFrame(self.countdown_button)
        self.countdown_right.setObjectName(u"countdown_right")
        sizePolicy.setHeightForWidth(
                self.countdown_right.sizePolicy().hasHeightForWidth()
                )
        self.countdown_right.setSizePolicy(sizePolicy)
        self.countdown_right.setLayoutDirection(Qt.LeftToRight)
        self.countdown_right.setFrameShape(QFrame.StyledPanel)
        self.countdown_right.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.countdown_right)
        self.horizontalLayout_12.setSpacing(0)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(15, 0, 5, 0)
        self.countdown_text = QPushButton(self.countdown_right)
        self.countdown_text.setObjectName(u"countdown_text")
        sizePolicy2.setHeightForWidth(
                self.countdown_text.sizePolicy().hasHeightForWidth()
                )
        self.countdown_text.setSizePolicy(sizePolicy2)
        self.countdown_text.setMinimumSize(QSize(60, 30))
        self.countdown_text.setMaximumSize(QSize(60, 30))
        self.countdown_text.setFont(font3)
        self.countdown_text.setStyleSheet(u"#usb_count{\n"
                                          "    background-color: rgb(229, "
                                          "137, 147);\n"
                                          "    color: rgb(252, 252, 252);\n"
                                          "    font-weight: 600;\n"
                                          "    text-align:center;\n"
                                          "    border-radius: 9.4px;\n"
                                          "}\n"
                                          ""
                                          )
        self.countdown_text.setIconSize(QSize(14, 14))
        self.countdown_text.setCheckable(False)

        self.horizontalLayout_12.addWidget(self.countdown_text, 0,
                                           Qt.AlignRight
                                           )

        self.horizontalLayout_10.addWidget(self.countdown_right, 0,
                                           Qt.AlignRight
                                           )

        self.verticalLayout_6.addWidget(self.countdown_button)

        self.gridLayout_2.addWidget(self.countdown, 1, 0, 1, 1, Qt.AlignBottom)

        self.verticalLayout_3.addWidget(self.prefs, 0,
                                        Qt.AlignHCenter | Qt.AlignBottom
                                        )

        self.supp = QFrame(self.widget)
        self.supp.setObjectName(u"supp")
        self.supp.setMinimumSize(QSize(0, 30))
        self.supp.setMaximumSize(QSize(16777215, 30))
        self.supp.setFrameShape(QFrame.StyledPanel)
        self.supp.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.supp)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.logo_frame = QFrame(self.supp)
        self.logo_frame.setObjectName(u"logo_frame")
        self.logo_frame.setMinimumSize(QSize(0, 0))
        self.logo_frame.setMaximumSize(QSize(16777215, 16777215))
        self.logo_frame.setFrameShape(QFrame.StyledPanel)
        self.logo_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.logo_frame)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.logo = QLabel(self.logo_frame)
        self.logo.setObjectName(u"logo")
        self.logo.setMinimumSize(QSize(84, 20))
        self.logo.setMaximumSize(QSize(84, 20))
        self.logo.setPixmap(QPixmap(u":/icns/light/swiftGuard-text-light.png"))
        self.logo.setScaledContents(True)

        self.horizontalLayout_5.addWidget(self.logo, 0,
                                          Qt.AlignLeft | Qt.AlignBottom
                                          )

        self.horizontalLayout_4.addWidget(self.logo_frame, 0, Qt.AlignLeft)

        self.ctrl_frame = QFrame(self.supp)
        self.ctrl_frame.setObjectName(u"ctrl_frame")
        self.ctrl_frame.setMinimumSize(QSize(85, 0))
        self.ctrl_frame.setMaximumSize(QSize(85, 16777215))
        self.ctrl_frame.setFrameShape(QFrame.StyledPanel)
        self.ctrl_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.ctrl_frame)
        self.horizontalLayout_6.setSpacing(11)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.settings_button = QPushButton(self.ctrl_frame)
        self.settings_button.setObjectName(u"settings_button")
        self.settings_button.setMinimumSize(QSize(22, 22))
        self.settings_button.setMaximumSize(QSize(22, 22))
        self.settings_button.setCursor(QCursor(Qt.PointingHandCursor))
        icon3 = QIcon()
        icon3.addFile(u":/icns/light/gear.svg", QSize(), QIcon.Normal,
                      QIcon.Off
                      )
        self.settings_button.setIcon(icon3)
        self.settings_button.setIconSize(QSize(16, 16))

        self.horizontalLayout_6.addWidget(self.settings_button)

        self.help_button = QPushButton(self.ctrl_frame)
        self.help_button.setObjectName(u"help_button")
        self.help_button.setMinimumSize(QSize(22, 22))
        self.help_button.setMaximumSize(QSize(22, 22))
        self.help_button.setCursor(QCursor(Qt.PointingHandCursor))
        icon4 = QIcon()
        icon4.addFile(u":/icns/light/questionmark.svg", QSize(), QIcon.Normal,
                      QIcon.Off
                      )
        self.help_button.setIcon(icon4)
        self.help_button.setIconSize(QSize(14, 14))

        self.horizontalLayout_6.addWidget(self.help_button)

        self.exit_button = QPushButton(self.ctrl_frame)
        self.exit_button.setObjectName(u"exit_button")
        self.exit_button.setMinimumSize(QSize(22, 22))
        self.exit_button.setMaximumSize(QSize(22, 22))
        self.exit_button.setCursor(QCursor(Qt.PointingHandCursor))
        icon5 = QIcon()
        icon5.addFile(u":/icns/light/xmark.svg", QSize(), QIcon.Normal,
                      QIcon.Off
                      )
        self.exit_button.setIcon(icon5)
        self.exit_button.setIconSize(QSize(14, 14))

        self.horizontalLayout_6.addWidget(self.exit_button)

        self.horizontalLayout_4.addWidget(self.ctrl_frame, 0,
                                          Qt.AlignRight | Qt.AlignBottom
                                          )

        self.verticalLayout_3.addWidget(self.supp, 0, Qt.AlignBottom)

        self.verticalLayout_2.addWidget(self.widget, 0, Qt.AlignTop)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
                QCoreApplication.translate("MainWindow", u"MainWindow", None)
                )
        self.usb_placeholder.setText(
                QCoreApplication.translate("MainWindow",
                                           u" No devices found ...",
                                           None
                                           )
                )
        self.usb_state.setText(
                QCoreApplication.translate("MainWindow", u"  Guarding", None)
                )
        self.usb_count.setText(
                QCoreApplication.translate("MainWindow", u"0", None)
                )
        self.usb_allowed.setText(
                QCoreApplication.translate("MainWindow", u"Allowed", None)
                )
        self.counter_left_button.setText(
                QCoreApplication.translate("MainWindow", u"Counter-Measure",
                                           None
                                           )
                )
        self.counter_icon.setText("")
        self.countdown_left_button.setText(
                QCoreApplication.translate("MainWindow", u"Countdown Timer",
                                           None
                                           )
                )
        self.countdown_text.setText(
                QCoreApplication.translate("MainWindow", u"15 s", None)
                )
        self.logo.setText("")
        self.settings_button.setText("")
        self.help_button.setText("")
        self.exit_button.setText("")
    # retranslateUi
