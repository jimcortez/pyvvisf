#ifndef JSONGUIINPUTAUDIOFFT_H
#define JSONGUIINPUTAUDIOFFT_H

#include "JSONGUIInputWidget.h"




namespace Ui {
	class JSONGUIInputAudioFFT;
}




class JSONGUIInputAudioFFTWidget : public JSONGUIInputWidget
{
	Q_OBJECT

public:
	explicit JSONGUIInputAudioFFTWidget(const JGMInputRef & inInput, JSONScrollWidget * inScrollWidget, QWidget *parent = nullptr);
	~JSONGUIInputAudioFFTWidget();
	
	virtual void prepareToBeDeleted() override;
	
	virtual void prepareUIItems() override;
	virtual void refreshUIItems() override;

private:
	Ui::JSONGUIInputAudioFFT *ui;
};

#endif // JSONGUIINPUTAUDIOFFT_H
