#ifndef GLBUFFERQWIDGET_H
#define GLBUFFERQWIDGET_H

#include "VVGL.hpp"
#include <mutex>
#include <QOpenGLWidget>

#ifdef Q_OS_MACOS
#include "DisplayLinkDriver.h"
#endif




class GLBufferQWidget : public QOpenGLWidget	{
	Q_OBJECT
	
public:
	GLBufferQWidget(QWidget * inParent=nullptr);
	~GLBufferQWidget();
	
	//	calls the start/stop slot on the appropriate thread
	void startRendering();
	void stopRendering();
	
	//QThread * getRenderThread();
	
	VVGL::GLContextRef glContextRef() { std::lock_guard<std::recursive_mutex> lock(ctxLock); return ctx; }
	void drawBuffer(const VVGL::GLBufferRef & inBuffer);
	VVGL::GLBufferRef getBuffer();
	
public slots:
	Q_SLOT void startRenderingSlot();
	Q_SLOT void stopRenderingSlot();
	Q_SLOT void aboutToQuit();
	
signals:
	
protected:
	//bool event(QEvent * inEvent) Q_DECL_OVERRIDE;
	void paintGL() Q_DECL_OVERRIDE;
	void initializeGL() Q_DECL_OVERRIDE;
	void resizeGL(int w, int h) Q_DECL_OVERRIDE;
	
private:
	void _renderNow();
	
private:
#ifdef Q_OS_MACOS
	DisplayLinkDriver		displayLinkDriver;	//	calling 'QOpenGLWidget::update' on macs breaks Qt: https://bugreports.qt.io/browse/QTBUG-73209
#endif
	std::recursive_mutex	ctxLock;
	VVGL::GLContextRef		ctx = nullptr;
	VVGL::GLSceneRef		scene = nullptr;
	QThread					*ctxThread = nullptr;
	VVGL::GLBufferRef			vao = nullptr;
	VVGL::Quad<VVGL::VertXYST>		lastVBOCoords;	//	the last coords used in the VBO associated with 'vao' (the VAO implicitly retains the VBO, so we only need to update it when the coords change- which we track with this)
	VVGL::GLBufferRef		buffer = nullptr;
	
	void stopRenderingImmediately();
	inline VVGL::GLBufferRef _getBuffer() const { return buffer; }
};




#endif // GLBUFFERQWIDGET_H
