#include "Highlighter.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>

#if defined(Q_OS_WIN)
#define __PRETTY_FUNCTION__ __FUNCSIG__
#endif




namespace SimpleSourceCodeEdit	{




Highlighter::Highlighter(QTextDocument * inParent)
	: QSyntaxHighlighter(inParent)
{
	//	configure some default comment start and end expressions
	commentSingleExpr = QRegularExpression("//[^\n]*");
	commentStartExpr = QRegularExpression("/\\*");
	commentEndExpr = QRegularExpression("\\*/");
	
	//xxxFmt.setFontWeight(QFont::Bold);
	/*
	plainTextFmt.setForeground(Qt::black);
	*/
	variablesFmt.setForeground(QColor("#aaffff"));
	typeAndClassNamesFmt.setForeground(QColor("#aa00ff"));
	functionsFmt.setForeground(QColor("#55aaff"));
	sdkFunctionsFmt.setForeground(QColor("#55aaff"));
	keywordsFmt.setForeground(QColor("#ffffff"));
	pragmasFmt.setForeground(QColor("#00ff00"));
	numbersFmt.setForeground(QColor("#ff3737"));
	quotationsFmt.setForeground(QColor("#ff3737"));
	commentFmt.setForeground(QColor("#ffc737"));
	
	bgSelTextFmt.setForeground(QColor("#000000"));
	bgSelTextFmt.setBackground(QColor("#ffff50"));
	
	loadColorsFromSettings();
}
void Highlighter::loadSyntaxDefinitionDocument(const QJsonDocument & inDocument)	{
	//qDebug() << __PRETTY_FUNCTION__;
	if (!inDocument.isObject()) {
		qDebug() << "\tERR: document is not a JSON object, bailing, " << __PRETTY_FUNCTION__;
		return;
	}
	
	loadColorsFromSettings();
	
	syntaxDocHighlightRules.clear();
	
	QJsonObject		tmpDocObj = inDocument.object();
	HighlightRule	tmpRule;
	
	if (tmpDocObj.contains("VARIABLES") && tmpDocObj["VARIABLES"].isArray())	{
		tmpRule.format = variablesFmt;
		QJsonArray		tmpArray = tmpDocObj["VARIABLES"].toArray();
		QString			tmpStr = QString("\\b(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")\\b");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("TYPE_AND_CLASS_NAMES") && tmpDocObj["TYPE_AND_CLASS_NAMES"].isArray())	{
		tmpRule.format = typeAndClassNamesFmt;
		QJsonArray		tmpArray = tmpDocObj["TYPE_AND_CLASS_NAMES"].toArray();
		QString			tmpStr = QString("\\b(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")\\b");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("FUNCTION_REGEXES") && tmpDocObj["FUNCTION_REGEXES"].isArray())	{
		tmpRule.format = functionsFmt;
		QJsonArray		tmpArray = tmpDocObj["FUNCTION_REGEXES"].toArray();
		QString			tmpStr = QString("(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("SDK_FUNCTIONS") && tmpDocObj["SDK_FUNCTIONS"].isArray())	{
		tmpRule.format = sdkFunctionsFmt;
		QJsonArray		tmpArray = tmpDocObj["SDK_FUNCTIONS"].toArray();
		QString			tmpStr = QString("\\b(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")\\b");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("KEYWORDS") && tmpDocObj["KEYWORDS"].isArray())	{
		tmpRule.format = keywordsFmt;
		QJsonArray		tmpArray = tmpDocObj["KEYWORDS"].toArray();
		QString			tmpStr = QString("\\b(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")\\b");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("PRAGMA_REGEXES") && tmpDocObj["PRAGMA_REGEXES"].isArray())	{
		tmpRule.format = pragmasFmt;
		QJsonArray		tmpArray = tmpDocObj["PRAGMA_REGEXES"].toArray();
		QString			tmpStr = QString("(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("NUMBER_REGEXES") && tmpDocObj["NUMBER_REGEXES"].isArray())	{
		tmpRule.format = numbersFmt;
		QJsonArray		tmpArray = tmpDocObj["NUMBER_REGEXES"].toArray();
		QString			tmpStr = QString("(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	if (tmpDocObj.contains("QUOTATION_REGEXES") && tmpDocObj["QUOTATION_REGEXES"].isArray())	{
		tmpRule.format = quotationsFmt;
		QJsonArray		tmpArray = tmpDocObj["QUOTATION_REGEXES"].toArray();
		QString			tmpStr = QString("(");
		int				tmpIndex = 0;
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				if (tmpIndex == 0)
					tmpStr.append( QString("(%1)").arg(tmpVal.toString()) );
				else
					tmpStr.append( QString("|(%1)").arg(tmpVal.toString()) );
				++tmpIndex;
			}
		}
		if (tmpIndex > 0)	{
			tmpStr.append(")");
			tmpRule.pattern = QRegularExpression(tmpStr);
			syntaxDocHighlightRules.append(tmpRule);
		}
	}
	
	
	//	this bit creates the same rules as above, but creates many small QRegularExpressions instead of a couple very long QRegularExpressions
	/*
	if (tmpDocObj.contains("VARIABLES") && tmpDocObj["VARIABLES"].isArray())	{
		tmpRule.format = variablesFmt;
		QJsonArray		tmpArray = tmpDocObj["VARIABLES"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(QString("\\b%1\\b").arg(tmpVal.toString()));
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("TYPE_AND_CLASS_NAMES") && tmpDocObj["TYPE_AND_CLASS_NAMES"].isArray())	{
		tmpRule.format = typeAndClassNamesFmt;
		QJsonArray		tmpArray = tmpDocObj["TYPE_AND_CLASS_NAMES"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(QString("\\b%1\\b").arg(tmpVal.toString()));
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("FUNCTION_REGEXES") && tmpDocObj["FUNCTION_REGEXES"].isArray())	{
		tmpRule.format = functionsFmt;
		QJsonArray		tmpArray = tmpDocObj["FUNCTION_REGEXES"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(tmpVal.toString());
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("SDK_FUNCTIONS") && tmpDocObj["SDK_FUNCTIONS"].isArray())	{
		tmpRule.format = sdkFunctionsFmt;
		QJsonArray		tmpArray = tmpDocObj["SDK_FUNCTIONS"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(QString("\\b%1\\b").arg(tmpVal.toString()));
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("KEYWORDS") && tmpDocObj["KEYWORDS"].isArray())	{
		tmpRule.format = keywordsFmt;
		QJsonArray		tmpArray = tmpDocObj["KEYWORDS"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(QString("\\b%1\\b").arg(tmpVal.toString()));
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("PRAGMA_REGEXES") && tmpDocObj["PRAGMA_REGEXES"].isArray())	{
		tmpRule.format = pragmasFmt;
		QJsonArray		tmpArray = tmpDocObj["PRAGMA_REGEXES"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(tmpVal.toString());
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("NUMBER_REGEXES") && tmpDocObj["NUMBER_REGEXES"].isArray())	{
		tmpRule.format = numbersFmt;
		QJsonArray		tmpArray = tmpDocObj["NUMBER_REGEXES"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(tmpVal.toString());
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	if (tmpDocObj.contains("QUOTATION_REGEXES") && tmpDocObj["QUOTATION_REGEXES"].isArray())	{
		tmpRule.format = quotationsFmt;
		QJsonArray		tmpArray = tmpDocObj["QUOTATION_REGEXES"].toArray();
		for (const QJsonValue & tmpVal : tmpArray)	{
			if (tmpVal.isString())	{
				tmpRule.pattern = QRegularExpression(tmpVal.toString());
				syntaxDocHighlightRules.append(tmpRule);
			}
		}
	}
	*/
	
	if (tmpDocObj.contains("SINGLE_LINE_COMMENT_REGEX") && tmpDocObj["SINGLE_LINE_COMMENT_REGEX"].isString())	{
		commentSingleExpr = QRegularExpression(tmpDocObj["SINGLE_LINE_COMMENT_REGEX"].toString());
	}
	if (tmpDocObj.contains("MULTI_LINE_COMMENT_START_REGEX") && tmpDocObj["MULTI_LINE_COMMENT_START_REGEX"].isString()) {
		//	no format to set here, we're not making a rule- just an expression!
		commentStartExpr = QRegularExpression(tmpDocObj["MULTI_LINE_COMMENT_START_REGEX"].toString());
	}
	if (tmpDocObj.contains("MULTI_LINE_COMMENT_END_REGEX") && tmpDocObj["MULTI_LINE_COMMENT_END_REGEX"].isString()) {
		//	no format to set here, we're not making a rule- just an expression!
		commentEndExpr = QRegularExpression(tmpDocObj["MULTI_LINE_COMMENT_END_REGEX"].toString());
	}
	
	if (tmpDocObj.contains("SINGLE_LINE_COMMENT_REGEX") && tmpDocObj["SINGLE_LINE_COMMENT_REGEX"].isString())	{
		tmpRule.format = commentFmt;
		tmpRule.pattern = QRegularExpression(tmpDocObj["SINGLE_LINE_COMMENT_REGEX"].toString());
		syntaxDocHighlightRules.append(tmpRule);
	}
}
void Highlighter::loadColorsFromSettings()	{
	QSettings		settings;
	
	if (!settings.contains("color_txt_bg"))	{
		QColor		tmpColor("#1a1a1a");
		settings.setValue("color_txt_bg", QVariant(tmpColor));
	}
	
	if (!settings.contains("color_txt_txt"))	{
		QColor		tmpColor("#b4b4b4");
		settings.setValue("color_txt_txt", QVariant(tmpColor));
	}
	
	if (!settings.contains("color_txt_seltxt"))	{
		QColor		tmpColor("#000000");
		settings.setValue("color_txt_seltxt", QVariant(tmpColor));
	}
	
	if (!settings.contains("color_txt_selbg"))	{
		QColor		tmpColor("#ffff50");
		settings.setValue("color_txt_selbg", QVariant(tmpColor));
	}
	
	if (!settings.contains("color_txt_seltxt_alt"))	{
		QColor		tmpColor("#000000");
		settings.setValue("color_txt_seltxt_alt", QVariant(tmpColor));
	}
	bgSelTextFmt.setForeground(settings.value("color_txt_seltxt_alt").value<QColor>());
	
	if (!settings.contains("color_txt_selbg_alt"))	{
		QColor		tmpColor("#999950");
		settings.setValue("color_txt_selbg_alt", QVariant(tmpColor));
	}
	bgSelTextFmt.setBackground(settings.value("color_txt_selbg_alt").value<QColor>());
	
	if (!settings.contains("color_txt_var"))	{
		QColor		tmpColor("#aaffff");
		settings.setValue("color_txt_var", QVariant(tmpColor));
	}
	variablesFmt.setForeground(settings.value("color_txt_var").value<QColor>());
	
	if (!settings.contains("color_txt_typeClass"))	{
		QColor		tmpColor("#aa00ff");
		settings.setValue("color_txt_typeClass", QVariant(tmpColor));
	}
	typeAndClassNamesFmt.setForeground(settings.value("color_txt_typeClass").value<QColor>());
	
	if (!settings.contains("color_txt_funcs"))	{
		QColor		tmpColor("#55aaff");
		settings.setValue("color_txt_funcs", QVariant(tmpColor));
	}
	functionsFmt.setForeground(settings.value("color_txt_funcs").value<QColor>());
	
	if (!settings.contains("color_txt_sdkFuncs"))	{
		QColor		tmpColor("#55aaff");
		settings.setValue("color_txt_sdkFuncs", QVariant(tmpColor));
	}
	sdkFunctionsFmt.setForeground(settings.value("color_txt_sdkFuncs").value<QColor>());
	
	if (!settings.contains("color_txt_keywords"))	{
		QColor		tmpColor("#ffffff");
		settings.setValue("color_txt_keywords", QVariant(tmpColor));
	}
	keywordsFmt.setForeground(settings.value("color_txt_keywords").value<QColor>());
	
	if (!settings.contains("color_txt_pragmas"))	{
		QColor		tmpColor("#00ff00");
		settings.setValue("color_txt_pragmas", QVariant(tmpColor));
	}
	pragmasFmt.setForeground(settings.value("color_txt_pragmas").value<QColor>());
	
	if (!settings.contains("color_txt_numbers"))	{
		QColor		tmpColor("#ff3737");
		settings.setValue("color_txt_numbers", QVariant(tmpColor));
	}
	numbersFmt.setForeground(settings.value("color_txt_numbers").value<QColor>());
	
	if (!settings.contains("color_txt_quotes"))	{
		QColor		tmpColor("#ff3737");
		settings.setValue("color_txt_quotes", QVariant(tmpColor));
	}
	quotationsFmt.setForeground(settings.value("color_txt_quotes").value<QColor>());
	
	if (!settings.contains("color_txt_comment"))	{
		QColor		tmpColor("#ffc737");
		settings.setValue("color_txt_comment", QVariant(tmpColor));
	}
	commentFmt.setForeground(settings.value("color_txt_comment").value<QColor>());
	
}
void Highlighter::setLocalVariableNames(const QStringList & inStrList)	{
	
	localVarHighlightRules.clear();
	
	HighlightRule	tmpRule;
	QString			tmpStr = QString("\\b(");
	int				tmpIndex = 0;
	for (const QString & inStr : inStrList)	{
		if (tmpIndex == 0)
			tmpStr.append( QString("(%1)").arg(inStr) );
		else
			tmpStr.append( QString("|(%1)").arg(inStr) );
		++tmpIndex;
	}
	if (tmpIndex > 0)	{
		tmpStr.append(")\\b");
		tmpRule.format = variablesFmt;
		tmpRule.pattern = QRegularExpression(tmpStr);
		localVarHighlightRules.append(tmpRule);
	}
}
void Highlighter::setSelectedText(const QString & inStr)	{
	//qDebug() << __PRETTY_FUNCTION__ << ", " << inStr;
	
	selTextHighlightRules.clear();
	
	if (inStr.length() < 1)
		return;
	
	HighlightRule	tmpRule;
	QString			tmpStr = QString("\\b(");
	tmpStr.append(inStr);
	tmpStr.append(")\\b");
	tmpRule.format = bgSelTextFmt;
	tmpRule.pattern = QRegularExpression(tmpStr);
	selTextHighlightRules.append(tmpRule);
}


void Highlighter::highlightBlock(const QString & inText)
{
	//qDebug() << __PRETTY_FUNCTION__ << ": " << inText;
	bool			isPlainText = true;
	//	first run through the local var highlight rules
	foreach (const HighlightRule & tmpRule, localVarHighlightRules)	{
		QRegularExpressionMatchIterator		matchIterator = tmpRule.pattern.globalMatch(inText);
		while (matchIterator.hasNext()) {
			QRegularExpressionMatch		tmpMatch = matchIterator.next();
			setFormat(tmpMatch.capturedStart(), tmpMatch.capturedLength(), tmpRule.format);
			isPlainText = false;
		}
	}
	//	run through all of the syntax highlight rules, checked the passed string against each
	foreach (const HighlightRule & tmpRule, syntaxDocHighlightRules) {
		QRegularExpressionMatchIterator		matchIterator = tmpRule.pattern.globalMatch(inText);
		while (matchIterator.hasNext()) {
			QRegularExpressionMatch		tmpMatch = matchIterator.next();
			setFormat(tmpMatch.capturedStart(), tmpMatch.capturedLength(), tmpRule.format);
			isPlainText = false;
		}
	}
	//	set the current block state
	setCurrentBlockState(HBS_OK);
	
	//	check this line- figure out if there's a single-line comment, and if so, the index where the single-line comment starts
	int		singleLineCommentStartIndex = -1;
	if (inText.contains(commentSingleExpr))	{
		singleLineCommentStartIndex = commentSingleExpr.match(inText).capturedStart();
		isPlainText = false;
	}
	
	//	if there isn't an open multi-line comment, look for the beginning of one in the passed text
	int		multiLineCommentStartIndex = 0;
	if (previousBlockState() != HBS_OpenComment)	{
		multiLineCommentStartIndex = inText.indexOf(commentStartExpr);
	}
	//	if the multi-line comment beginning occurred after the single-line comment start, we need to ignore it!
	if (multiLineCommentStartIndex>=0 && singleLineCommentStartIndex>=0 && multiLineCommentStartIndex>singleLineCommentStartIndex)
		multiLineCommentStartIndex = -1;
	
	//	if we found the beginning of a multi-line comment...
	while (multiLineCommentStartIndex >= 0) {
		QRegularExpressionMatch		tmpMatch = commentEndExpr.match(inText, multiLineCommentStartIndex);
		int			endIndex = tmpMatch.capturedStart();
		int			commentLength = 0;
		if (endIndex == -1) {
			setCurrentBlockState(HBS_OpenComment);
			commentLength = inText.length() - multiLineCommentStartIndex;
		}
		else	{
			commentLength = endIndex - multiLineCommentStartIndex + tmpMatch.capturedLength();
		}
		setFormat(multiLineCommentStartIndex, commentLength, commentFmt);
		multiLineCommentStartIndex = inText.indexOf(commentStartExpr, multiLineCommentStartIndex + commentLength);
		isPlainText = false;
	}
	
	//	selected text needs to be highlighted last!
	foreach (const HighlightRule & tmpRule, selTextHighlightRules)	{
		QRegularExpressionMatchIterator		matchIterator = tmpRule.pattern.globalMatch(inText);
		while (matchIterator.hasNext())	{
			QRegularExpressionMatch		tmpMatch = matchIterator.next();
			setFormat(tmpMatch.capturedStart(), tmpMatch.capturedLength(), tmpRule.format);
			isPlainText = false;
		}
	}
	
	/*
	//	if this is plain text...
	if (isPlainText)	{
		setFormat(0, inText.length(), plainTextFmt);
	}
	*/
}




}	//	namespace SimpleSourceCodeEdit
