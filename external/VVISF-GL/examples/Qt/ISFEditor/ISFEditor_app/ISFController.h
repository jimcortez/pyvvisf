#ifndef ISFCONTROLLER_H
#define ISFCONTROLLER_H

#include <mutex>
#include <vector>
#include <utility>

#include <QSpacerItem>
#include <QFileSystemWatcher>

#include "VVISF.hpp"
#include "ISFUIItem.h"
#include "ISFGLBufferQWidget.h"
#include "VVGLRenderQThread.h"




using namespace std;




class ISFController : public QObject
{
	Q_OBJECT
public:
	ISFController();
	~ISFController();
	
	void loadFile(const QString & inPathToLoad);
	void setRenderSize(const VVGL::Size & inSize) { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); _renderSize=inSize; }
	VVGL::Size renderSize() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return _renderSize; }
	//ISFSceneRef getScene() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return scene; }
	//ISFDocRef getCurrentDoc() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return (scene==nullptr)?nullptr:scene->doc(); }
	VVISF::ISFDocRef getCurrentDoc() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return currentDoc; }
	QString getCompiledVertexShaderString() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return (scene==nullptr) ? QString() : QString::fromStdString( scene->vertexShaderString() ); }
	QString getCompiledFragmentShaderString() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return (scene==nullptr) ? QString() : QString::fromStdString( scene->fragmentShaderString() ); }
	vector<pair<int,string>> getSceneJSONErrors() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return sceneJSONErrors; }
	vector<pair<int,string>> getSceneVertErrors() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return sceneVertErrors; }
	vector<pair<int,string>> getSceneFragErrors() { std::lock_guard<std::recursive_mutex> lockGuard(sceneLock); return sceneFragErrors; }
	
	void threadedRenderCallback();
	VVGLRenderQThread * renderThread() {
		return _renderThread;
	}
	VVGL::GLBufferPoolRef renderThreadBufferPool() { return (_renderThread==nullptr)?nullptr:_renderThread->bufferPool(); }
	VVGL::GLTexToTexCopierRef renderThreadTexCopier() { return (_renderThread==nullptr)?nullptr:_renderThread->texCopier(); }

public slots:
	//	the widget sends a signal to this slot every time it's about to redraw
	Q_SLOT void widgetRedrawSlot();
	
private:
	VVGL::Size			_renderSize = VVGL::Size(640.0,480.0);
	
	std::recursive_mutex	sceneLock;	//	used to lock the 'scene'-related vars below
	QFileSystemWatcher		*sceneFileWatcher = nullptr;
	VVISF::ISFDocRef				currentDoc = nullptr;
	VVISF::ISFSceneRef				scene = nullptr;	//	this is the main scene doing all the rendering!
	bool					sceneIsFilter = false;
	vector<pair<int,string>>		sceneJSONErrors;
	vector<pair<int,string>>		sceneVertErrors;
	vector<pair<int,string>>		sceneFragErrors;
	bool					needToLoadFiles = false;	//	this is how we pass contexts between threads: we check this and move the ctx on the relevant thread.
	bool					loadingFiles = false;
	
	QString					targetFile;
	
	QList<QPointer<ISFUIItem>>		sceneItemArray;
	
	QSpacerItem				*spacerItem = nullptr;	//	must be explicitly freed!
	
	VVGLRenderQThread		*_renderThread = nullptr;
	//GLContextRef			_renderThreadCtx = nullptr;
	//GLBufferPoolRef			_renderThreadBufferPool = nullptr;
	//GLTexToTexCopierRef		_renderThreadTexCopier = nullptr;

private:
	void populateLoadingWindowUI();
	void reloadTargetFile();
private slots:
	void aboutToQuit();
};




//	gets the global singleton for this class, which is created in main()
ISFController * GetISFController();




#endif // ISFCONTROLLER_H
