#import "DifferingGLVersionsAppDelegate.h"
//#import "GLBufferPool_CocoaAdditions.h"




#define NSTOVVGLRECT(n) (VVGL::Rect(n.origin.x, n.origin.y, n.size.width, n.size.height))
#define NSTOVVGLSIZE(n) (VVGL::Size(n.width, n.height))




@interface DifferingGLVersionsAppDelegate ()
@property (assign,readwrite) VVGL::Quad<VertXYST> lastVBOCoords;
@end

using namespace std;




@implementation DifferingGLVersionsAppDelegate


- (id) init	{
	self = [super init];
	if (self != nil)	{
		legacyGLCtx = CreateNewGLContextRef(NULL, CreateCompatibilityGLPixelFormat());
		legacyBufferPool = make_shared<GLBufferPool>(legacyGLCtx);
		legacyGLScene = CreateGLSceneRefUsing(legacyGLCtx->newContextSharingMe());
		
		modernGLCtx = CreateNewGLContextRef(NULL, CreateGL4PixelFormat());
		modernBufferPool = make_shared<GLBufferPool>(modernGLCtx);
		modernGLScene = CreateGLSceneRefUsing(modernGLCtx->newContextSharingMe());
		
		[self setDate:[NSDate date]];
		
		[self initLegacyGL];
		[self initModernGL];
	}
	return self;
}


- (void) initLegacyGL	{
	//	make an NSImage from the PNG included with the app, create a GLBufferRef from it
	NSImage			*tmpImg = [[NSImage alloc] initWithContentsOfFile:[[NSBundle mainBundle] pathForResource:@"SampleImg" ofType:@"png"]];
	GLBufferRef	imgBuffer = CreateBufferForNSImage(tmpImg, false, legacyBufferPool);
	[tmpImg release];
	tmpImg = nil;
	
	void			*selfPtr = (void*)self;
	
	legacyGLScene->setRenderCallback([selfPtr, imgBuffer](const GLScene & n)	{
		if (imgBuffer == nullptr)	{
			NSLog(@"\t\terr: legacy imgBuffer null, bailing");
			return;
		}
		//	populate a tex quad with the geometry & tex coords
		Quad<VertXYST>			texQuad;
		VVGL::Size				sceneSize = n.orthoSize();
		//VVGL::Rect				geoRect(0, 0, sceneSize.width, sceneSize.height);
		VVGL::Rect				geoRect = ResizeRect(imgBuffer->srcRect, VVGL::Rect(0,0,sceneSize.width,sceneSize.height), SizingMode_Fit);
		VVGL::Rect				texRect = imgBuffer->glReadySrcRect();
		texQuad.populateGeo(geoRect);
		texQuad.populateTex(texRect, imgBuffer->flipped);
		
		//	draw the GLBufferRef we created from the PNG, using the tex quad
		glEnable(imgBuffer->desc.target);
		glEnableClientState(GL_VERTEX_ARRAY);
		glEnableClientState(GL_TEXTURE_COORD_ARRAY);
		glVertexPointer(2, GL_FLOAT, texQuad.stride(), &texQuad);
		glTexCoordPointer(2, GL_FLOAT, texQuad.stride(), &texQuad.bl.tex[0]);
		glBindTexture(imgBuffer->desc.target, imgBuffer->name);
		glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
		glBindTexture(imgBuffer->desc.target, 0);
		
		//	we're going to draw a quad "over" the image, using the NSDate property of self to determine how long the app's been running
		double					timeSinceStart = [[(id)selfPtr date] timeIntervalSinceNow] * -1.;
		double					opacity = fmod(timeSinceStart, 1.);
		Quad<VertXY>			colorQuad;
		colorQuad.populateGeo(geoRect);
		glDisableClientState(GL_TEXTURE_COORD_ARRAY);
		glVertexPointer(2, GL_FLOAT, texQuad.stride(), &texQuad);
		glColor4f(0., 0., 0., opacity);
		glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
	});
}


- (void) initModernGL	{
	//	make an NSImage from the PNG included with the app, create a GLBufferRef from it
	NSImage			*tmpImg = [[NSImage alloc] initWithContentsOfFile:[[NSBundle mainBundle] pathForResource:@"SampleImg" ofType:@"png"]];
	GLBufferRef	imgBuffer = CreateBufferForNSImage(tmpImg, false, modernBufferPool);
	[tmpImg release];
	tmpImg = nil;
	
	void			*selfPtr = (void*)self;
	
	string			vsString("\r\
#version 330 core\r\
in vec3		inXYZ;\r\
in vec2		inST;\r\
uniform mat4	vvglOrthoProj;\r\
out vec2		programST;\r\
void main()	{\r\
	gl_Position = vec4(inXYZ.x, inXYZ.y, inXYZ.z, 1.0) * vvglOrthoProj;\r\
	programST = inST;\r\
}\r\
");
	string			fsString("\r\
#version 330 core\r\
in vec2		programST;\r\
uniform sampler2D		inputImage;\r\
uniform sampler2DRect	inputImageRect;\r\
uniform int		isRectTex;\r\
uniform float	fadeVal;\r\
out vec4		FragColor;\r\
void main()	{\r\
if (isRectTex==0)\r\
	FragColor = vec4(0,0,0,1);\r\
else if (isRectTex==1)\r\
	FragColor = texture(inputImage,programST);\r\
else\r\
	FragColor = texture(inputImageRect,programST);\r\
FragColor *= (1.-fadeVal);\r\
}\r\
");
	modernGLScene->setVertexShaderString(vsString);
	modernGLScene->setFragmentShaderString(fsString);
	
	//	we're going to create a couple vars on the stack here- the vars themselves are shared 
	//	ptrs, so when they're copied by value in the callback blocks the copies will refer to 
	//	the same underlying vars, which will be retained until these callback blocks are 
	//	destroyed and shared between the callback lambdas...
	GLCachedAttribRef		xyzAttr = make_shared<GLCachedAttrib>("inXYZ");
	GLCachedAttribRef		stAttr = make_shared<GLCachedAttrib>("inST");
	GLCachedUniRef		inputImageUni = make_shared<GLCachedUni>("inputImage");
	GLCachedUniRef		inputImageRectUni = make_shared<GLCachedUni>("inputImageRect");
	GLCachedUniRef		isRectTexUni = make_shared<GLCachedUni>("isRectTex");
	GLCachedUniRef		fadeValUni = make_shared<GLCachedUni>("fadeVal");
	
	//	the render prep callback needs to cache the location of the vertex attributes and uniforms
	modernGLScene->setRenderPrepCallback([xyzAttr,stAttr,inputImageUni,inputImageRectUni,isRectTexUni,fadeValUni,self](const GLScene & n, const bool & inReshaped, const bool & inPgmChanged)	{
		//cout << __PRETTY_FUNCTION__ << endl;
		if (inPgmChanged)	{
			//	cache all the locations for the vertex attributes & uniform locations
			GLint				myProgram = n.program();
			xyzAttr->cacheTheLoc(myProgram);
			stAttr->cacheTheLoc(myProgram);
			inputImageUni->cacheTheLoc(myProgram);
			inputImageRectUni->cacheTheLoc(myProgram);
			isRectTexUni->cacheTheLoc(myProgram);
			fadeValUni->cacheTheLoc(myProgram);
			
			//	make a new VAO
			[self setVAO:CreateVAO(true, modernBufferPool)];
		}
	});
	
	//	the render callback passes all the data to the GL program
	modernGLScene->setRenderCallback([imgBuffer,xyzAttr,stAttr,inputImageUni,inputImageRectUni,isRectTexUni,fadeValUni,selfPtr](const GLScene & n)	{
		//cout << __PRETTY_FUNCTION__ << endl;
		if (imgBuffer == nullptr)
			return;
		
		//	clear
		glClearColor(0., 0., 0., 1.);
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

		VVGL::Size			orthoSize = n.orthoSize();
		VVGL::Rect			boundsRect(0, 0, orthoSize.width, orthoSize.height);
		VVGL::Rect			geometryRect = ResizeRect(imgBuffer->srcRect, boundsRect, SizingMode_Fit);
		Quad<VertXYST>		targetQuad;
		targetQuad.populateGeo(geometryRect);
		targetQuad.populateTex((imgBuffer==nullptr) ? geometryRect : imgBuffer->glReadySrcRect(), (imgBuffer==nullptr) ? false : imgBuffer->flipped);
		
		//	pass the 2D texture to the program (if there's a 2D texture)
		glActiveTexture(GL_TEXTURE0);
		glBindTexture(GLBuffer::Target_2D, (imgBuffer!=nullptr && imgBuffer->desc.target==GLBuffer::Target_2D) ? imgBuffer->name : 0);
		glBindTexture(GLBuffer::Target_Rect, 0);
		if (inputImageUni->loc >= 0)	{
			glUniform1i(inputImageUni->loc, 0);
		}
		//	pass the RECT texture to the program (if there's a RECT texture)
		glActiveTexture(GL_TEXTURE1);
		glBindTexture(GLBuffer::Target_2D, 0);
		glBindTexture(GLBuffer::Target_Rect, (imgBuffer!=nullptr && imgBuffer->desc.target==GLBuffer::Target_Rect) ? imgBuffer->name : 0);
		if (inputImageRectUni->loc >= 0)	{
			glUniform1i(inputImageRectUni->loc, 1);
		}
		//	pass an int to the program that indicates whether we're passing no texture (0), a 2D texture (1) or a RECT texture (2)
		if (isRectTexUni->loc >= 0)	{
			if (imgBuffer == nullptr)
				glUniform1i(isRectTexUni->loc, 0);
			else	{
				switch (imgBuffer->desc.target)	{
				case GLBuffer::Target_2D:
					glUniform1i(isRectTexUni->loc, 1);
					break;
				case GLBuffer::Target_Rect:
					glUniform1i(isRectTexUni->loc, 2);
					break;
				default:
					glUniform1i(isRectTexUni->loc, 0);
					break;
				}
			}
		}
		//	pass the fade val to the program
		if (fadeValUni->loc >= 0)	{
			double					timeSinceStart = [[(id)selfPtr date] timeIntervalSinceNow] * -1.;
			GLfloat					opacity = fmod(timeSinceStart, 1.);
			glUniform1f(fadeValUni->loc, opacity);
		}
		
		//	bind the VAO
		GLBufferRef		tmpVAO = [(id)selfPtr vao];
		glBindVertexArray(tmpVAO->name);
		
		uint32_t			vbo = 0;
		if ([(id)selfPtr lastVBOCoords] != targetQuad)	{
			//	make a new VBO to contain vertex + texture coord data
			glGenBuffers(1, &vbo);
			glBindBuffer(GL_ARRAY_BUFFER, vbo);
			glBufferData(GL_ARRAY_BUFFER, sizeof(targetQuad), (void*)&targetQuad, GL_STATIC_DRAW);
			//	configure the attribute pointers to use the VBO
			if (xyzAttr->loc >= 0)	{
				glVertexAttribPointer(xyzAttr->loc, 2, GL_FLOAT, GL_FALSE, targetQuad.stride(), BUFFER_OFFSET(targetQuad.geoOffset()));
				xyzAttr->enable();
			}
			if (stAttr->loc >= 0)	{
				glVertexAttribPointer(stAttr->loc, 2, GL_FLOAT, GL_FALSE, targetQuad.stride(), BUFFER_OFFSET(targetQuad.texOffset()));
				stAttr->enable();
			}
		}
		
		//	draw
		glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
		//	un-bind the VAO
		glBindVertexArray(0);
		
		if ([(id)selfPtr lastVBOCoords] != targetQuad)	{
			//	delete the VBO we made earlier...
			glDeleteBuffers(1, &vbo);
			//	update the vbo coords ivar (we don't want to update the VBO contents every pass)
			[(id)selfPtr setLastVBOCoords:targetQuad];
		}
	});
}


- (void)applicationDidFinishLaunching:(NSNotification *)aNotification	{
	[legacyBufferView setSharedGLContext:legacyGLCtx];
	[modernBufferView setSharedGLContext:modernGLCtx];
	
	//	make the displaylink, which will drive rendering
	CVReturn				err = kCVReturnSuccess;
	CGOpenGLDisplayMask		totalDisplayMask = 0;
	GLint					virtualScreen = 0;
	GLint					displayMask = 0;
	NSOpenGLPixelFormat		*format = [[[NSOpenGLPixelFormat alloc] initWithCGLPixelFormatObj:legacyGLCtx->pxlFmt] autorelease];
	
	for (virtualScreen=0; virtualScreen<[format numberOfVirtualScreens]; ++virtualScreen)	{
		[format getValues:&displayMask forAttribute:NSOpenGLPFAScreenMask forVirtualScreen:virtualScreen];
		totalDisplayMask |= displayMask;
	}
	err = CVDisplayLinkCreateWithOpenGLDisplayMask(totalDisplayMask, &displayLink);
	if (err)	{
		NSLog(@"\t\terr %d creating display link in %s",err,__func__);
		displayLink = NULL;
	}
	else	{
		CVDisplayLinkSetOutputCallback(displayLink, displayLinkCallback, self);
		CVDisplayLinkStart(displayLink);
	}
}
//	this method is called from the displaylink callback
- (void) renderCallback	{
	//NSLog(@"%s",__func__);
	
	NSRect				legacyFrame = [legacyBufferView frame];
	GLBufferRef		legacyTex = legacyGLScene->createAndRenderABuffer(NSTOVVGLSIZE(legacyFrame.size), legacyBufferPool);
	[legacyBufferView drawBuffer:legacyTex];
	legacyBufferPool->housekeeping();
	
	NSRect				modernFrame = [modernBufferView frame];
	GLBufferRef		modernTex = modernGLScene->createAndRenderABuffer(NSTOVVGLSIZE(modernFrame.size), modernBufferPool);
	[modernBufferView drawBuffer:modernTex];
	modernBufferPool->housekeeping();
}


@synthesize date;
@synthesize vao;
@synthesize lastVBOCoords;


@end




CVReturn displayLinkCallback(CVDisplayLinkRef displayLink, 
	const CVTimeStamp *inNow, 
	const CVTimeStamp *inOutputTime, 
	CVOptionFlags flagsIn, 
	CVOptionFlags *flagsOut, 
	void *displayLinkContext)
{
	NSAutoreleasePool		*pool =[[NSAutoreleasePool alloc] init];
	[(DifferingGLVersionsAppDelegate *)displayLinkContext renderCallback];
	[pool release];
	return kCVReturnSuccess;
}
