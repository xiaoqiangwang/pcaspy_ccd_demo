import QtQuick 2.0
import CSDataQuick.Components 1.0

BaseWindow {
    width: 500
    height: 620
    CSText {
        id: text1
        x: 65
        y: 19
        text: "Exposure"
    }

    CSTextEntry {
        id: textEntry
        x: 144
        y: 18
        width: 80
        height: 20
        source: "iMott:AcquireTime"
    }

    CSText {
        id: text2
        x: 80
        y: 45
        text: "Cycles"
    }

    CSTextEntry {
        id: textEntry1
        x: 144
        y: 44
        width: 80
        source: "iMott:NumExposures"
    }

    CSText {
        id: text3
        x: 8
        y: 88
        width: 131
        height: 18
        text: "File Path"
        align: Text.AlignRight
    }

    CSTextEntry {
        id: textEntry2
        x: 143
        y: 87
        width: 341
        height: 20
        format: TextFormat.String
        source: "iMott:FilePath"
    }

    CSText {
        id: text4
        x: 8
        y: 114
        width: 131
        height: 18
        text: "File Name"
        align: Text.AlignRight
    }

    CSTextEntry {
        id: textEntry3
        x: 143
        y: 113
        width: 341
        height: 20
        format: TextFormat.String
        source: "iMott:FileName"
    }

    CSText {
        id: text5
        x: 8
        y: 140
        width: 131
        height: 18
        text: "Next File #"
        align: Text.AlignRight
    }

    CSTextEntry {
        id: textEntry4
        x: 143
        y: 139
        width: 110
        height: 20
        source: "iMott:FileNumber"
    }

    CSText {
        id: text6
        x: 8
        y: 196
        width: 130
        height: 18
        text: "Auto Incerement"
        align: Text.AlignRight
    }

    CSMenu {
        id: menu
        x: 144
        y: 190
        width: 80
        source: "iMott:AutoIncrement"
    }

    CSText {
        id: text7
        x: 240
        y: 192
        width: 79
        height: 18
        text: "Auto Save"
        align: Text.AlignRight
    }

    CSMenu {
        id: menu1
        x: 325
        y: 189
        width: 80
        source: "iMott:AutoSave"
    }

    CSMessageButton {
        id: messageButton
        x: 438
        y: 189
        width: 50
        text: "Save"
        onMessage: "1"
        source: "iMott:WriteFile"
    }

    CSMessageButton {
        id: messageButton1
        x: 325
        y: 18
        width: 71
        height: 25
        text: "Start"
        onMessage: "1"
        source: "iMott:Acquire"
    }

    CSMessageButton {
        id: messageButton2
        x: 413
        y: 18
        width: 71
        height: 25
        text: "Stop"
        onMessage: "0"
        source: "iMott:Acquire"
    }

    CSTextUpdate {
        id: textUpdate
        x: 346
        y: 46
        width: 131
        height: 18
        format: TextFormat.String
        align: Text.AlignHCenter
        colorMode: ColorMode.Alarm
        source: "iMott:DetectorState_RBV"
    }

    CSText {
        id: text8
        x: 8
        y: 164
        width: 131
        height: 18
        text: "Last filename"
        align: Text.AlignRight
    }

    CSTextUpdate {
        id: textUpdate1
        x: 250
        y: 46
        width: 47
        height: 18
        source: "iMott:NumExposuresCounter_RBV"
    }

    CSTextUpdate {
        id: textUpdate2
        x: 143
        y: 164
        width: 341
        height: 18
        align: Text.AlignLeft
        format: TextFormat.String
        source: "iMott:FullFileName_RBV"
    }

    CSOval {
        id: oval
        x: 485
        y: 90
        width: 15
        height: 15
        dynamicAttribute.channel: "iMott:FilePathExists_RBV"
        colorMode: ColorMode.Alarm
    }

    CSADImage {
        id: ad1
        x: 25
        y: 250
        width: 450
        height: 350
        source: 'iMott:'
    }
}
