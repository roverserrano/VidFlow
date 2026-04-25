pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore

ApplicationWindow {
    id: window
    width: 1180
    height: 820
    minimumWidth: 760
    minimumHeight: 620
    visible: true
    title: "VidFlow"

    Material.theme: Material.Dark
    Material.accent: Material.Cyan

    property color bgColor: "#0a0f1a"
    property color surfaceColor: "#111827"
    property color surfaceSoftColor: "#172033"
    property color borderColor: "#2a3446"
    property color textColor: "#f8fafc"
    property color mutedColor: "#9aa7b8"
    property color accentColor: "#22d3ee"
    property color successColor: "#22c55e"
    property color warningColor: "#f59e0b"
    property color dangerColor: "#ef4444"

    property string selectedFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
    property var mediaInfo: null
    property bool analyzing: false
    property string toastMessage: ""
    property string toastLevel: "info"

    function findJobIndex(jobId) {
        for (let i = 0; i < jobsModel.count; i++) {
            if (jobsModel.get(i).job_id === jobId) {
                return i
            }
        }
        return -1
    }

    function upsertJob(job) {
        const index = findJobIndex(job.job_id)
        if (index === -1) {
            jobsModel.insert(0, job)
        } else {
            jobsModel.set(index, job)
        }
    }

    function showToast(level, message) {
        toastLevel = level
        toastMessage = message
        toastBox.visible = true
        toastTimer.restart()
    }

    function statusText(status) {
        switch (status) {
        case "completed": return "Completado"
        case "error": return "Error"
        case "processing": return "Procesando"
        case "downloading": return "Descargando"
        case "preparing": return "Preparando"
        case "queued": return "En cola"
        case "canceled": return "Cancelado"
        default: return status
        }
    }

    function statusColor(status) {
        switch (status) {
        case "completed": return successColor
        case "error": return dangerColor
        case "processing": return warningColor
        case "downloading": return accentColor
        case "preparing": return "#38bdf8"
        case "queued": return "#64748b"
        case "canceled": return "#a78bfa"
        default: return "#64748b"
        }
    }

    function canCancel(status) {
        return status === "queued" || status === "preparing" || status === "downloading" || status === "processing"
    }

    function selectedFormat() {
        if (formatCombo.currentIndex < 0 || formatCombo.currentIndex >= formatModel.count) {
            return null
        }
        return formatModel.get(formatCombo.currentIndex)
    }

    function percentText(percent) {
        return percent >= 0 ? percent.toFixed(1) + "%" : "Calculando..."
    }

    FolderDialog {
        id: folderDialog
        title: "Selecciona la carpeta de destino"
        onAccepted: selectedFolder = folderDialog.selectedFolder.toString().replace("file://", "")
    }

    Timer {
        id: toastTimer
        interval: 3200
        repeat: false
        onTriggered: toastBox.visible = false
    }

    ListModel { id: formatModel }
    ListModel { id: jobsModel }

    ListModel {
        id: modeModel
        ListElement { label: "Video"; value: "video" }
        ListElement { label: "Audio"; value: "audio" }
    }

    ListModel {
        id: compatibilityModel
        ListElement { label: "Compatible MP4"; value: "compatible" }
        ListElement { label: "Original"; value: "original" }
    }

    ListModel {
        id: audioFormatModel
        ListElement { label: "MP3"; value: "mp3" }
        ListElement { label: "M4A"; value: "m4a" }
        ListElement { label: "OPUS"; value: "opus" }
        ListElement { label: "WAV"; value: "wav" }
    }

    Connections {
        target: appBridge

        function onAnalysisStarted() {
            analyzing = true
            mediaInfo = null
            formatModel.clear()
            statusLabel.text = "Analizando URL..."
        }

        function onAnalysisFinished(payload) {
            analyzing = false
            mediaInfo = JSON.parse(payload)
            statusLabel.text = "Análisis completado"
            formatModel.clear()

            for (let i = 0; i < mediaInfo.formats.length; i++) {
                const f = mediaInfo.formats[i]
                formatModel.append({
                    label: f.label || f.resolution,
                    value: f.plan,
                    note: f.note || "",
                    filesize_text: f.filesize_text || "—",
                    compatibility: f.compatibility || "good"
                })
            }

            if (formatModel.count > 0) {
                formatCombo.currentIndex = 0
            }
        }

        function onAnalysisError(message) {
            analyzing = false
            statusLabel.text = "Error: " + message
        }

        function onDownloadAdded(payload) {
            upsertJob(JSON.parse(payload))
        }

        function onDownloadUpdated(payload) {
            upsertJob(JSON.parse(payload))
        }

        function onToastRequested(level, message) {
            showToast(level, message)
        }
    }

    background: Rectangle { color: bgColor }

    ScrollView {
        id: pageScroll
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Item {
            width: pageScroll.availableWidth
            implicitHeight: pageContent.implicitHeight + 40

            ColumnLayout {
                id: pageContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 20
                spacing: 16

                Rectangle {
                    Layout.fillWidth: true
                    radius: 8
                    color: surfaceColor
                    border.color: borderColor
                    border.width: 1
                    implicitHeight: headerLayout.implicitHeight + 28

                    RowLayout {
                        id: headerLayout
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 12

                        Rectangle {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            radius: 8
                            color: accentColor

                            Label {
                                anchors.centerIn: parent
                                text: "V"
                                color: "#06111f"
                                font.bold: true
                                font.pixelSize: 22
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Label {
                                text: "VidFlow"
                                color: textColor
                                font.pixelSize: 26
                                font.bold: true
                            }

                            Label {
                                text: "TikTok · Facebook · YouTube"
                                color: mutedColor
                                font.pixelSize: 13
                            }
                        }

                        BusyIndicator {
                            running: analyzing
                            visible: analyzing
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                        }
                    }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: window.width < 980 ? 1 : 2
                    columnSpacing: 16
                    rowSpacing: 16

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 680
                        spacing: 16

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 8
                            color: surfaceColor
                            border.color: borderColor
                            border.width: 1
                            implicitHeight: inputLayout.implicitHeight + 28

                            ColumnLayout {
                                id: inputLayout
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 12

                                Label {
                                    text: "URL"
                                    color: textColor
                                    font.bold: true
                                    font.pixelSize: 16
                                }

                                TextField {
                                    id: urlField
                                    Layout.fillWidth: true
                                    placeholderText: "https://..."
                                    selectByMouse: true
                                    enabled: !analyzing
                                    onAccepted: appBridge.analyzeUrl(text)
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: window.width < 820 ? 1 : 3
                                    columnSpacing: 10
                                    rowSpacing: 10

                                    Button {
                                        id: analyzeButton
                                        Layout.fillWidth: true
                                        text: analyzing ? "Analizando" : "Analizar"
                                        enabled: !analyzing
                                        onClicked: appBridge.analyzeUrl(urlField.text)
                                    }

                                    Button {
                                        Layout.fillWidth: true
                                        text: "Elegir carpeta"
                                        onClicked: folderDialog.open()
                                    }

                                    Button {
                                        Layout.fillWidth: true
                                        text: "Abrir carpeta"
                                        enabled: selectedFolder.length > 0
                                        onClicked: appBridge.openFolder(selectedFolder)
                                    }
                                }

                                TextField {
                                    Layout.fillWidth: true
                                    readOnly: true
                                    text: selectedFolder
                                    placeholderText: "Carpeta de destino"
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 8
                                    color: surfaceSoftColor
                                    border.color: borderColor
                                    border.width: 1
                                    implicitHeight: statusTextLabel.implicitHeight + 18

                                    Label {
                                        id: statusTextLabel
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.margins: 10
                                        text: statusLabel.text
                                        color: mutedColor
                                        wrapMode: Text.Wrap
                                    }
                                }

                                Label {
                                    id: statusLabel
                                    visible: false
                                    text: "Esperando URL..."
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            visible: mediaInfo !== null
                            radius: 8
                            color: surfaceColor
                            border.color: borderColor
                            border.width: 1
                            implicitHeight: mediaLayout.implicitHeight + 28

                            ColumnLayout {
                                id: mediaLayout
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 14

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 14

                                    Rectangle {
                                        Layout.preferredWidth: window.width < 820 ? 190 : 260
                                        Layout.preferredHeight: window.width < 820 ? 108 : 146
                                        radius: 8
                                        color: surfaceSoftColor
                                        border.color: borderColor
                                        border.width: 1
                                        clip: true

                                        Image {
                                            anchors.fill: parent
                                            source: mediaInfo && mediaInfo.thumbnail ? mediaInfo.thumbnail : ""
                                            fillMode: Image.PreserveAspectCrop
                                            asynchronous: true
                                        }

                                        Label {
                                            anchors.centerIn: parent
                                            visible: !mediaInfo || !mediaInfo.thumbnail
                                            text: "Sin miniatura"
                                            color: mutedColor
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        Label {
                                            text: mediaInfo ? mediaInfo.title : ""
                                            color: textColor
                                            font.pixelSize: 21
                                            font.bold: true
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }

                                        Label {
                                            text: mediaInfo ? mediaInfo.extractor + " · " + mediaInfo.duration_text : ""
                                            color: mutedColor
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: window.width < 860 ? 1 : 2
                                    columnSpacing: 10
                                    rowSpacing: 10

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 6

                                        Label {
                                            text: "Modo"
                                            color: textColor
                                            font.bold: true
                                        }

                                        ComboBox {
                                            id: modeCombo
                                            Layout.fillWidth: true
                                            model: modeModel
                                            textRole: "label"
                                            valueRole: "value"
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 6
                                        visible: modeCombo.currentValue === "video"

                                        Label {
                                            text: "Compatibilidad"
                                            color: textColor
                                            font.bold: true
                                        }

                                        ComboBox {
                                            id: compatibilityCombo
                                            Layout.fillWidth: true
                                            model: compatibilityModel
                                            textRole: "label"
                                            valueRole: "value"
                                        }
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    visible: modeCombo.currentValue === "video"

                                    Label {
                                        text: "Calidad"
                                        color: textColor
                                        font.bold: true
                                    }

                                    ComboBox {
                                        id: formatCombo
                                        Layout.fillWidth: true
                                        model: formatModel
                                        textRole: "label"
                                        valueRole: "value"
                                        enabled: formatModel.count > 0
                                    }

                                    Label {
                                        Layout.fillWidth: true
                                        text: selectedFormat() ? selectedFormat().note + " · " + selectedFormat().filesize_text : "No hay formatos de video disponibles"
                                        color: selectedFormat() && selectedFormat().compatibility === "variable" ? warningColor : mutedColor
                                        wrapMode: Text.Wrap
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    visible: modeCombo.currentValue === "audio"

                                    Label {
                                        text: "Formato de audio"
                                        color: textColor
                                        font.bold: true
                                    }

                                    ComboBox {
                                        id: audioFormatCombo
                                        Layout.fillWidth: true
                                        model: audioFormatModel
                                        textRole: "label"
                                        valueRole: "value"
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: modeCombo.currentValue === "audio" ? "Descargar audio" : "Descargar video"
                                    enabled: mediaInfo !== null && (modeCombo.currentValue === "audio" || formatModel.count > 0)
                                    onClicked: {
                                        const isAudio = modeCombo.currentValue === "audio"
                                        appBridge.downloadMedia(
                                            mediaInfo.webpage_url,
                                            selectedFolder,
                                            isAudio ? "" : (formatCombo.currentValue || ""),
                                            isAudio,
                                            audioFormatCombo.currentValue || "mp3",
                                            mediaInfo.title,
                                            compatibilityCombo.currentValue || "compatible"
                                        )
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 420
                        Layout.fillHeight: false
                        radius: 8
                        color: surfaceColor
                        border.color: borderColor
                        border.width: 1
                        implicitHeight: downloadsLayout.implicitHeight + 28

                        ColumnLayout {
                            id: downloadsLayout
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 12

                            RowLayout {
                                Layout.fillWidth: true

                                Label {
                                    text: "Descargas"
                                    color: textColor
                                    font.pixelSize: 18
                                    font.bold: true
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: jobsModel.count > 0 ? jobsModel.count + "" : ""
                                    color: mutedColor
                                }
                            }

                            Rectangle {
                                visible: jobsModel.count === 0
                                Layout.fillWidth: true
                                radius: 8
                                color: surfaceSoftColor
                                border.color: borderColor
                                border.width: 1
                                implicitHeight: 128

                                Label {
                                    anchors.centerIn: parent
                                    width: parent.width - 28
                                    text: "Sin descargas"
                                    color: mutedColor
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }

                            ListView {
                                visible: jobsModel.count > 0
                                Layout.fillWidth: true
                                Layout.preferredHeight: Math.min(contentHeight, window.width < 980 ? 420 : 620)
                                model: jobsModel
                                spacing: 10
                                clip: true

                                delegate: Rectangle {
                                    required property string job_id
                                    required property string title
                                    required property string folder
                                    required property string status
                                    required property double percent
                                    required property string speed_text
                                    required property string eta_text
                                    required property string bytes_text
                                    required property string message

                                    width: ListView.view.width
                                    radius: 8
                                    color: surfaceSoftColor
                                    border.color: borderColor
                                    border.width: 1
                                    implicitHeight: jobLayout.implicitHeight + 24

                                    ColumnLayout {
                                        id: jobLayout
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 9

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            Label {
                                                text: title
                                                color: textColor
                                                font.bold: true
                                                wrapMode: Text.Wrap
                                                Layout.fillWidth: true
                                            }

                                            Rectangle {
                                                Layout.preferredWidth: Math.max(92, badgeLabel.implicitWidth + 18)
                                                Layout.preferredHeight: 26
                                                radius: 6
                                                color: statusColor(status)

                                                Label {
                                                    id: badgeLabel
                                                    anchors.centerIn: parent
                                                    text: statusText(status)
                                                    color: status === "processing" ? "#111827" : "white"
                                                    font.bold: true
                                                    font.pixelSize: 12
                                                }
                                            }
                                        }

                                        Label {
                                            text: message
                                            color: mutedColor
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }

                                        ProgressBar {
                                            Layout.fillWidth: true
                                            from: 0
                                            to: 1
                                            value: percent >= 0 ? percent / 100.0 : 0
                                            indeterminate: percent < 0 && canCancel(status)
                                        }

                                        GridLayout {
                                            Layout.fillWidth: true
                                            columns: window.width < 980 ? 2 : 4
                                            columnSpacing: 10
                                            rowSpacing: 4

                                            Label {
                                                text: percentText(percent)
                                                color: mutedColor
                                            }

                                            Label {
                                                text: speed_text
                                                color: mutedColor
                                            }

                                            Label {
                                                text: "ETA " + eta_text
                                                color: mutedColor
                                            }

                                            Label {
                                                Layout.fillWidth: true
                                                text: bytes_text
                                                color: mutedColor
                                                elide: Text.ElideRight
                                            }
                                        }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            Button {
                                                text: "Cancelar"
                                                visible: canCancel(status)
                                                onClicked: appBridge.cancelDownload(job_id)
                                            }

                                            Button {
                                                text: "Abrir carpeta"
                                                onClicked: appBridge.openFolder(folder)
                                            }

                                            Item { Layout.fillWidth: true }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: toastBox
        visible: false
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
        radius: 8
        color: toastLevel === "error"
               ? "#7f1d1d"
               : toastLevel === "success"
                 ? "#14532d"
                 : "#164e63"
        border.color: toastLevel === "error"
                      ? dangerColor
                      : toastLevel === "success"
                        ? successColor
                        : accentColor
        border.width: 1
        width: Math.min(window.width - 40, 430)
        height: toastText.implicitHeight + 24
        z: 999

        Label {
            id: toastText
            anchors.centerIn: parent
            width: parent.width - 24
            text: toastMessage
            color: "white"
            wrapMode: Text.Wrap
        }
    }
}
