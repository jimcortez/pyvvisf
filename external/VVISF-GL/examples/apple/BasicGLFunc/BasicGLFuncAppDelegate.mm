#import "BasicGLFuncAppDelegate.h"
//#import "GLBufferPool_CocoaAdditions.h"




@interface BasicGLFuncAppDelegate ()
@property (assign,readwrite) VVGL::Quad<VertXYZSTRGBA> lastVBOCoords;
@end

using namespace std;




@implementation BasicGLFuncAppDelegate


- (id) init	{
	self = [super init];
	if (self != nil)	{
		
		//	make the shared context using the vsn of GL you need to target.  all GL contexts are going to share this so they can share textures/etc with one another
		sharedContext = CreateNewGLContextRef(NULL, CreateCompatibilityGLPixelFormat());
		//sharedContext = CreateNewGLContextRef(NULL, CreateGL4PixelFormat());
		
		//	make the global buffer pool.  if there's a global buffer pool, calls to create textures/etc will be shorter.  the global buffer pool will use the shared context to create any GL resources
		CreateGlobalBufferPool(sharedContext);
		
		//	make the GL scene we're going to use to render to texture (the texture will then be drawn in a view)
		glScene = CreateGLSceneRefUsing(sharedContext->newContextSharingMe());
		//	set up the GL context- this will vary significantly based on the version of GL you chose to use when making the shared context above
		if (glScene->glVersion() == GLVersion_2)
			[self initForGL2];
		else
			[self initForModernGL];
		
		[self setDate:[NSDate date]];
	}
	return self;
}


- (void)applicationDidFinishLaunching:(NSNotification *)aNotification	{
	//	pass the shared context to the buffer view (view has its own ctx, so it needs to be in the same sharegroup to be able to draw the passed texture)
	[bufferView setSharedGLContext:sharedContext];
	//	make the displaylink, which will drive rendering
	CVReturn				err = kCVReturnSuccess;
	CGOpenGLDisplayMask		totalDisplayMask = 0;
	GLint					virtualScreen = 0;
	GLint					displayMask = 0;
	NSOpenGLPixelFormat		*format = [[[NSOpenGLPixelFormat alloc] initWithCGLPixelFormatObj:sharedContext->pxlFmt] autorelease];
	
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
	//	tell the GL scene to allocate and render itself to a buffer
	GLBufferRef		newTex = glScene->createAndRenderABuffer();
	//	draw the GL texture i just rendered in the buffer view
	[bufferView drawBuffer:newTex];
	//	tell the buffer pool to do its housekeeping (releases any "old" resources in the pool that have been sticking around for a while)
	GetGlobalBufferPool()->housekeeping();
}


- (void) initForGL2	{
	//	make an NSImage from the PNG included with the app, create a GLBufferRef from it
	NSImage			*tmpImg = [[NSImage alloc] initWithContentsOfFile:[[NSBundle mainBundle] pathForResource:@"SampleImg" ofType:@"png"]];
	GLBufferRef	imgBuffer = CreateBufferForNSImage(tmpImg);
	[tmpImg release];
	tmpImg = nil;
	
	void			*selfPtr = (void*)self;
	
	glScene->setRenderPrepCallback([&](const GLScene & n, const bool inReshaped, const bool inPgmChanged)	{
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
	});
	glScene->setRenderCallback([selfPtr, imgBuffer](const GLScene & n)	{
		//	figure out how long we've been rendering, modulate it at one second
		double					timeSinceStart = [[(id)selfPtr date] timeIntervalSinceNow] * -1.;
		double					fillerColorVal = fmod(timeSinceStart, 1.);
		//	populate a tex quad with the geometry, tex, and color vals
		Quad<VertXYZSTRGBA>		texQuad;
		VVGL::Size				sceneSize = n.orthoSize();
		VVGL::Rect				geoRect = ResizeRect(imgBuffer->srcRect, VVGL::Rect(0,0,sceneSize.width,sceneSize.height), SizingMode_Fit);
		VVGL::Rect				texRect = imgBuffer->glReadySrcRect();
		texQuad.populateGeo(geoRect);
		texQuad.populateTex(texRect, imgBuffer->flipped);
		texQuad.bl.color = GLColor(1., 1., 1., 1.);
		texQuad.tl.color = GLColor(1., fillerColorVal, fillerColorVal, 1.);
		texQuad.tr.color = GLColor(fillerColorVal, 1., fillerColorVal, 1.);
		texQuad.br.color = GLColor(fillerColorVal, fillerColorVal, 1., 1.);
		
		//	draw the GLBufferRef we created from the PNG, using the tex quad
		glEnable(imgBuffer->desc.target);
		glEnableClientState(GL_VERTEX_ARRAY);
		glEnableClientState(GL_TEXTURE_COORD_ARRAY);
		glEnableClientState(GL_COLOR_ARRAY);
		
		glVertexPointer(texQuad.bl.geo.numComponents(), GL_FLOAT, texQuad.stride(), &texQuad.bl.geo[0]);
		glTexCoordPointer(texQuad.bl.tex.numComponents(), GL_FLOAT, texQuad.stride(), &texQuad.bl.tex[0]);
		glColorPointer(texQuad.bl.color.numComponents(), GL_FLOAT, texQuad.stride(), &texQuad.bl.color[0]);
		
		glBindTexture(imgBuffer->desc.target, imgBuffer->name);
		
		glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
		
		glBindTexture(imgBuffer->desc.target, 0);
	});
}
- (void) initForModernGL	{
	//	make an NSImage from the PNG included with the app, create a GLBufferRef from it
	NSImage			*tmpImg = [[NSImage alloc] initWithContentsOfFile:[[NSBundle mainBundle] pathForResource:@"SampleImg" ofType:@"png"]];
	GLBufferRef	imgBuffer = CreateBufferForNSImage(tmpImg);
	[tmpImg release];
	tmpImg = nil;
	
	void			*selfPtr = (void*)self;
	
	string			vsString("\r\
#version 330 core\r\
in vec3		inXYZ;\r\
in vec2		inST;\r\
in vec4		inRGBA;\r\
uniform mat4	vvglOrthoProj;\r\
out vec2		programST;\r\
out vec4		programRGBA;\r\
void main()	{\r\
	gl_Position = vec4(inXYZ.x, inXYZ.y, inXYZ.z, 1.0) * vvglOrthoProj;\r\
	programST = inST;\r\
	programRGBA = inRGBA;\r\
}\r\
");
	string			fsString("\r\
#version 330 core\r\
in vec2		programST;\r\
in vec4		programRGBA;\r\
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
FragColor *= programRGBA;\r\
}\r\
");
	glScene->setVertexShaderString(vsString);
	glScene->setFragmentShaderString(fsString);
	
	//	we're going to create a couple vars on the stack here- the vars themselves are shared 
	//	ptrs, so when they're copied by value in the callback blocks the copies will refer to 
	//	the same underlying vars, which will be retained until these callback blocks are 
	//	destroyed and shared between the callback lambdas...
	GLCachedAttribRef		xyzAttr = make_shared<GLCachedAttrib>("inXYZ");
	GLCachedAttribRef		stAttr = make_shared<GLCachedAttrib>("inST");
	GLCachedAttribRef		rgbaAttr = make_shared<GLCachedAttrib>("inRGBA");
	GLCachedUniRef		inputImageUni = make_shared<GLCachedUni>("inputImage");
	GLCachedUniRef		inputImageRectUni = make_shared<GLCachedUni>("inputImageRect");
	GLCachedUniRef		isRectTexUni = make_shared<GLCachedUni>("isRectTex");
	GLCachedUniRef		fadeValUni = make_shared<GLCachedUni>("fadeVal");
	
	//	the render prep callback needs to cache the location of the vertex attributes and uniforms
	glScene->setRenderPrepCallback([xyzAttr,stAttr,rgbaAttr,inputImageUni,inputImageRectUni,isRectTexUni,fadeValUni,self](const GLScene & n, const bool & inReshaped, const bool & inPgmChanged)	{
		//cout << __PRETTY_FUNCTION__ << endl;
		if (inPgmChanged)	{
			//	cache all the locations for the vertex attributes & uniform locations
			GLint				myProgram = n.program();
			xyzAttr->cacheTheLoc(myProgram);
			stAttr->cacheTheLoc(myProgram);
			rgbaAttr->cacheTheLoc(myProgram);
			inputImageUni->cacheTheLoc(myProgram);
			inputImageRectUni->cacheTheLoc(myProgram);
			isRectTexUni->cacheTheLoc(myProgram);
			fadeValUni->cacheTheLoc(myProgram);
			
			//	make a new VAO
			[self setVAO:CreateVAO(true)];
		}
	});
	
	//	the render callback passes all the data to the GL program
	glScene->setRenderCallback([imgBuffer,xyzAttr,stAttr,rgbaAttr,inputImageUni,inputImageRectUni,isRectTexUni,fadeValUni,selfPtr](const GLScene & n)	{
		//cout << __PRETTY_FUNCTION__ << endl;
		if (imgBuffer == nullptr)
			return;
		
		//	figure out how long we've been rendering, modulate it at one second
		double					timeSinceStart = [[(id)selfPtr date] timeIntervalSinceNow] * -1.;
		double					fillerColorVal = fmod(timeSinceStart, 1.);
		
		//	clear
		glClearColor(0., 0., 0., 1.);
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
		
		VVGL::Size			orthoSize = n.orthoSize();
		VVGL::Rect			boundsRect(0, 0, orthoSize.width, orthoSize.height);
		VVGL::Rect			geometryRect = ResizeRect(imgBuffer->srcRect, boundsRect, SizingMode_Fit);
		Quad<VertXYZSTRGBA>		targetQuad;
		targetQuad.populateGeo(geometryRect);
		targetQuad.populateTex((imgBuffer==nullptr) ? geometryRect : imgBuffer->glReadySrcRect(), (imgBuffer==nullptr) ? false : imgBuffer->flipped);
		targetQuad.bl.color = GLColor(1., 1., 1., 1.);
		targetQuad.tl.color = GLColor(1., fillerColorVal, fillerColorVal, 1.);
		targetQuad.tr.color = GLColor(fillerColorVal, 1., fillerColorVal, 1.);
		targetQuad.br.color = GLColor(fillerColorVal, fillerColorVal, 1., 1.);
		
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
				glVertexAttribPointer(xyzAttr->loc, targetQuad.bl.geo.numComponents(), GL_FLOAT, GL_FALSE, targetQuad.stride(), BUFFER_OFFSET(targetQuad.geoOffset()));
				xyzAttr->enable();
			}
			if (stAttr->loc >= 0)	{
				glVertexAttribPointer(stAttr->loc, targetQuad.bl.tex.numComponents(), GL_FLOAT, GL_FALSE, targetQuad.stride(), BUFFER_OFFSET(targetQuad.texOffset()));
				stAttr->enable();
			}
			if (rgbaAttr->loc >= 0)	{
				glVertexAttribPointer(rgbaAttr->loc, targetQuad.bl.color.numComponents(), GL_FLOAT, GL_FALSE, targetQuad.stride(), BUFFER_OFFSET(targetQuad.colorOffset()));
				rgbaAttr->enable();
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
	[(BasicGLFuncAppDelegate *)displayLinkContext renderCallback];
	[pool release];
	return kCVReturnSuccess;
}
