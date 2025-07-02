#include "MediaFile.h"

#include <QFileInfo>




int QVariantMediaFileUserType = -1;




void RegisterVariantTypes()	{
	if (QVariantMediaFileUserType < 0)	{
		QVariantMediaFileUserType = qRegisterMetaType<MediaFile>();
		//QMetaType::registerComparators<MediaFile>();
		//QMetaType::registerEqualsComparator<MediaFile>();
	}
	if (QVariant_videoSourceMenuItem_userType < 0)	{
		QVariant_videoSourceMenuItem_userType = qRegisterMetaType<QCameraInfo>();
		//QMetaType::registerComparators<QCameraInfo>();
	}
}




MediaFile::MediaFile(const Type & inType, const QString & inName, const QString & inOtherString) :
	_type(inType),
	_name(inName),
	resourceLocator(inOtherString)
{
	RegisterVariantTypes();
}
MediaFile::MediaFile(const Type & inType, const QString & inPath) : _type(inType), resourceLocator(inPath)	{
	RegisterVariantTypes();
	switch (_type)	{
	case Type_None:
	case Type_Cam:	//	should never happen
	case Type_App:	//	should never happen
		_name = QString("None");
		break;
	case Type_Mov:
	case Type_Img:
	case Type_ISF:
		_name = QFileInfo(resourceLocator.toString()).baseName();
		break;
	}
}
MediaFile::MediaFile(const QCameraInfo & inCameraInfo) : _type(Type_Cam), resourceLocator(QVariant::fromValue(inCameraInfo)) {
	RegisterVariantTypes();
	switch (_type)	{
	case Type_None:
	case Type_App:	//	should never happen
	case Type_Mov:	//	should never happen
	case Type_Img:	//	should never happen
	case Type_ISF:	//	should never happen
		_name = QString("None");
	case Type_Cam:
		_name = resourceLocator.value<QCameraInfo>().description();
		break;
	}
}




QString MediaFile::StringForType(const MediaFile::Type & n)	{
	switch (n)	{
	case Type_None:		return QString("X");
	case Type_App:		return QString("A");
	case Type_Mov:		return QString("M");
	case Type_Img:		return QString("I");
	case Type_Cam:		return QString("C");
	case Type_ISF:		return QString("S");
	}
	return QString("?");
}




QString MediaFile::name() const	{
	return _name;
}
QString MediaFile::path() const	{
	if (_type==Type_Mov || _type==Type_Img || _type==Type_ISF)
		return resourceLocator.toString();
	return QString();
}
QString MediaFile::syphonUUID() const	{
	if (_type==Type_App)
		return resourceLocator.toString();
	return QString();
}
QCameraInfo MediaFile::cameraInfo() const	{
	if (_type==Type_Cam)
		return resourceLocator.value<QCameraInfo>();
	return QCameraInfo();
}




bool MediaFile::operator==(const MediaFile & n) const	{
	//qDebug() << __PRETTY_FUNCTION__ << "... self is " << *this << ", passed is " << n;
	if (_type!=n.type())
		return false;
	
	switch (_type)	{
	case Type_None:
		return true;
	case Type_Cam:
		return (cameraInfo() == n.cameraInfo());
	case Type_Mov:
	case Type_Img:
	case Type_ISF:
		return (path() == n.path());
	case Type_App:
		return (syphonUUID() == n.syphonUUID());
	}
	
	return false;
}
bool MediaFile::operator<(const MediaFile & n) const	{
	Type		compType = n.type();
	if (_type != compType)	{
		return (static_cast<int>(_type) < static_cast<int>(compType));
	}
	
	switch (_type)	{
	case Type_None:
		return false;
	case Type_Cam:
		return (name() < n.name());
	case Type_Mov:
	case Type_Img:
	case Type_ISF:
		return (path() < n.path());
	case Type_App:
		return (name() < n.name());
	}
	return false;
}

