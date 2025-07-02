#import "ISFQL_RendererAppDelegate.h"
#import "ISFQLRendererAgent.h"
//#import <VVBufferPool/VVBufferPool.h>

#import "VVLogger.h"

//#include "VVGL.hpp"
//#include "VVISF.hpp"
#include "VVGLContextCacheItem.h"




//VVBuffer		*_globalColorBars = nil;
//ISFGLScene		*_swizzleScene = nil;



#define LOCK OSSpinLockLock
#define UNLOCK OSSpinLockUnlock




@implementation ISFQL_RendererAppDelegate


- (id) init	{
	//NSLog(@"%s",__func__);
	//[[VVLogger alloc] initWithFolderName:@"ISFQL_Renderer" maxNumLogs:20];
//#if !DEBUG
	//[[VVLogger globalLogger] redirectLogs];
//#endif
	
	self = [super init];
	if (self != nil)	{
		ttlLock = OS_SPINLOCK_INIT;
		ttlTimer = nil;
		
		//	spawn a thread- the listener will run on this thread
		[NSThread detachNewThreadSelector:@selector(threadLaunch:) toTarget:self withObject:nil];
		
		[self resetTTLTimer];
	}
	//NSLog(@"\t\t%s - FINISHED",__func__);
	return self;
}
- (void)applicationDidFinishLaunching:(NSNotification *)aNotification {
	//NSLog(@"%s",__func__);
	//NSLog(@"\t\t%s - FINISHED",__func__);
}
- (void)applicationWillTerminate:(NSNotification *)aNotification {
	//NSLog(@"%s",__func__);
}
- (void) dealloc	{
	//NSLog(@"%s",__func__);
	[super dealloc];
}


#pragma mark renderer timeout methods


- (void) noMoreRenderersTimer:(NSTimer *)t	{
	//NSLog(@"%s",__func__);
	exit(0);
}
- (void) resetTTLTimer	{
	//NSLog(@"%s",__func__);
	LOCK(&ttlLock);
	if (ttlTimer != nil)	{
		[ttlTimer invalidate];
		ttlTimer = nil;
	}
	UNLOCK(&ttlLock);
	
	dispatch_async(dispatch_get_main_queue(), ^{
		LOCK(&ttlLock);
		if (ttlTimer != nil)
			[ttlTimer invalidate];
		ttlTimer = [NSTimer
			scheduledTimerWithTimeInterval:5.
			target:self
			selector:@selector(noMoreRenderersTimer:)
			userInfo:nil
			repeats:NO];
		UNLOCK(&ttlLock);
	});
}


#pragma mark XPC and XPC thread-related


- (void) threadLaunch:(id)sender	{
	//NSLog(@"%s",__func__);
	NSAutoreleasePool		*pool = [[NSAutoreleasePool alloc] init];
	NSXPCListener			*listener = [[NSXPCListener alloc] initWithMachServiceName:@"com.vidvox.ISFQL-Renderer"];
	[listener setDelegate:self];
	[listener resume];
	[pool release];
	pool = nil;
	//NSLog(@"\t\t%s - FINISHED",__func__);
}
- (BOOL) listener:(NSXPCListener *)listener shouldAcceptNewConnection:(NSXPCConnection *)newConnection	{
	//NSLog(@"%s",__func__);
	//	reset the TTL timer
	[self resetTTLTimer];
	
	//	make a local object for the new connection- this object must be freed later, or it will leak!
	ISFQLRendererAgent		*exportedObj = [[ISFQLRendererAgent alloc] init];
	[newConnection setExportedInterface:[NSXPCInterface interfaceWithProtocol:@protocol(ISFQLAgentService)]];
	[newConnection setExportedObject:exportedObj];
	//	we don't want to free this now- the agent will free itself either when it's done rendering a frame or when it times out
	//[exportedObj release];
	
	[newConnection setRemoteObjectInterface:[NSXPCInterface interfaceWithProtocol:@protocol(ISFQLService)]];
	[newConnection resume];
	
	[exportedObj setConn:newConnection];
	[exportedObj setDelegate:self];
	//NSLog(@"\t\t%s - FINISHED",__func__);
	return YES;
	
}


#pragma mark ISFQLRendererAgentDelegate


//	this method is called 
- (void) agentKilled:(id)renderer	{
	//NSLog(@"%s",__func__);
	[self resetTTLTimer];
}


@end
