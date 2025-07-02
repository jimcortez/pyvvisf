QT += gui
QT += opengl multimedia

TARGET = VVISFTestApp
TEMPLATE = app

CONFIG += c++14
#CONFIG -= app_bundle

# The following define makes your compiler emit warnings if you use
# any feature of Qt which as been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS




# these libs require an ISF_SDK define
DEFINES += VVGL_SDK_QT




# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
	../common/GLBufferQWindow.cpp \
	../common/VVGLRenderQThread.cpp \
    VVISFTestApp.cpp

HEADERS += \
	../common/GLBufferQWindow.h \
	../common/VVGLRenderQThread.h




# additions for VVGL lib
win32:CONFIG(release, debug|release): LIBS += -L$$OUT_PWD/../VVGL/release/ -lVVGL
else:win32:CONFIG(debug, debug|release): LIBS += -L$$OUT_PWD/../VVGL/debug/ -lVVGL
else:unix: LIBS += -L$$OUT_PWD/../VVGL/ -lVVGL

# additions for VVISF lib
win32:CONFIG(release, debug|release): LIBS += -L$$OUT_PWD/../VVISF/release/ -lVVISF
else:win32:CONFIG(debug, debug|release): LIBS += -L$$OUT_PWD/../VVISF/debug/ -lVVISF
else:unix: LIBS += -L$$OUT_PWD/../VVISF/ -lVVISF

INCLUDEPATH += $$_PRO_FILE_PWD_/../../../VVGL/include
INCLUDEPATH += $$_PRO_FILE_PWD_/../../../VVISF/include
INCLUDEPATH += $$_PRO_FILE_PWD_/../common
INCLUDEPATH += $$_PRO_FILE_PWD_/../
#DEPENDPATH += $$PWD/../VVGL
#DEPENDPATH += $$PWD/../VVISF




# make sure the rpath includes both ways of getting libs
QMAKE_RPATHDIR = @executable_path/../Frameworks
QMAKE_RPATHDIR += @loader_path/../Frameworks




# additions for GLEW
#unix: LIBS += -L/usr/local/lib/ -lGLEW
#INCLUDEPATH += /usr/local/include
#DEPENDPATH += /usr/local/include
#unix: PRE_TARGETDEPS += /usr/local/lib/libGLEW.a
unix: LIBS += -L$$_PRO_FILE_PWD_/../../../external/GLEW/mac_x86_64/ -lGLEW
win32: LIBS += -L$$_PRO_FILE_PWD_/../../../external/GLEW/win_x64/ -lglew32 -lopengl32
INCLUDEPATH += $$_PRO_FILE_PWD_/../../../external/GLEW/include
DEPENDPATH += $$_PRO_FILE_PWD_/../../../external/GLEW/include
unix: PRE_TARGETDEPS += $$_PRO_FILE_PWD_/../../../external/GLEW/mac_x86_64/libGLEW.dylib
win32: PRE_TARGETDEPS += $$_PRO_FILE_PWD_/../../../external/GLEW/win_x64/glew32.dll




RESOURCES += \
    resources.qrc




# macs need some assembly for deployment
mac	{
	QMAKE_INFO_PLIST = Info.plist
	
	CONFIG(debug, debug|release)	{
		# intentionally blank, debug builds don't need any work (build & run works just fine)
	}
	# release builds need to have the libs bundled up and macdeployqt executed on the output app package to relink them
	else	{
		framework_dir = $$OUT_PWD/$$TARGET\.app/Contents/Frameworks
		QMAKE_POST_LINK += echo "****************************";
		QMAKE_POST_LINK += mkdir -pv $$framework_dir;
		QMAKE_POST_LINK += cp -vaRf $$_PRO_FILE_PWD_/../../../external/GLEW/mac_x86_64/libGLEW*.dylib $$framework_dir;
		QMAKE_POST_LINK += cp -vaRf $$OUT_PWD/../VVGL/libVVGL*.dylib $$framework_dir;
		QMAKE_POST_LINK += cp -vaRf $$OUT_PWD/../VVISF/libVVISF*.dylib $$framework_dir;
		QMAKE_POST_LINK += macdeployqt $$OUT_PWD/$$TARGET\.app;
	}
}
win32	{
	CONFIG(debug, debug|release)	{
		#	intentionally blank, debug builds don't need any work (build & run works just fine)
	}
	#	release builds need to have the libs copied to the dest dir, and windeployqt executed on the output app
	else	{
		MY_DEPLOY_DIR = $$shell_quote($$shell_path("$${OUT_PWD}/release"))

		QMAKE_POST_LINK += copy $$shell_quote($$shell_path($$OUT_PWD/../VVGL/release/VVGL.dll)) $${MY_DEPLOY_DIR} $$escape_expand(\n)
		QMAKE_POST_LINK += copy $$shell_quote($$shell_path($$OUT_PWD/../VVISF/release/VVISF.dll)) $${MY_DEPLOY_DIR} $$escape_expand(\n)
		QMAKE_POST_LINK += copy $$shell_quote($$shell_path($$OUT_PWD/../../../external/GLEW/win_x64/glew32.dll)) $${MY_DEPLOY_DIR} $$escape_expand(\n)

		MY_WINDEPLOYQT = $$shell_quote($$shell_path($$[QT_INSTALL_BINS]/windeployqt))
		MY_TARGET_EXE = $$shell_quote($$shell_path("$${OUT_PWD}/release/$${TARGET}.exe"))
		QMAKE_POST_LINK += $${MY_WINDEPLOYQT} --compiler-runtime --verbose 3 $${MY_TARGET_EXE} $$escape_expand(\n)
	}
}
