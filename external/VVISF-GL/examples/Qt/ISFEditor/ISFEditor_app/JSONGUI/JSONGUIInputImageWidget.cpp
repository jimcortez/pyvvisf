#include "JSONGUIInputImageWidget.h"
#include "ui_JSONGUIInputImageWidget.h"




JSONGUIInputImageWidget::JSONGUIInputImageWidget(const JGMInputRef & inRef, JSONScrollWidget * inScrollWidget, QWidget *parent) :
	JSONGUIInputWidget(inRef, inScrollWidget, parent),
	ui(new Ui::JSONGUIInputImage)
{
	ui->setupUi(this);
	
	if (_input != nullptr)	{
		prepareUIItems();
		refreshUIItems();
	}
}
JSONGUIInputImageWidget::~JSONGUIInputImageWidget()
{
	delete ui;
}
void JSONGUIInputImageWidget::prepareToBeDeleted()	{
	QObject::disconnect((ui->dragLabel), 0, 0, 0);
	QObject::disconnect((ui->inputNameEdit), 0, 0, 0);
	QObject::disconnect((ui->labelField), 0, 0, 0);
	QObject::disconnect((ui->typePUB), 0, 0, 0);
	QObject::disconnect((ui->deleteLabel), 0, 0, 0);
}




void JSONGUIInputImageWidget::prepareUIItems() {
	//	have my super prepare the UI items common to all of these
	prepareDragLabel( (ui->dragLabel) );
	prepareInputNameEdit( (ui->inputNameEdit) );
	prepareLabelField( (ui->labelField) );
	prepareTypeCBox( (ui->typePUB) );
	prepareDeleteLabel( (ui->deleteLabel) );
	
	//	prepare the UI items specific to this input
}
void JSONGUIInputImageWidget::refreshUIItems() {
	//	have my super refresh the UI items common to all of these
	refreshInputNameEdit( (ui->inputNameEdit) );
	refreshLabelField( (ui->labelField) );
	refreshTypeCBox( (ui->typePUB) );
	prepareDeleteLabel( (ui->deleteLabel) );
	
	//	refresh the UI items specific to this input
}
