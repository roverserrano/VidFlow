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
    visible: true
    title: "VidFlow"

    Material.theme: Material.Dark
    Material.accent: Material.Blue

    property color bgColor: "#0b1220"
    property color panelColor: "#111827"
    property color panelSoftColor: "#0f172a"
    property color borderColor: "#1f2937"
    property color textColor: "#ffffff"
    property color mutedColor: "#94a3b8"
    property color softTextColor: "#cbd5e1"
    property color accentColor: "#3b82f6"

    property string selectedFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
    property var mediaInfo: null
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
            jobsModel.append(job)
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

    function badgeColor(status) {
        switch (status) {
        case "completed": return "#22c55e"
        case "error": return "#ef4444"
        case "processing": return "#f59e0b"
        case "downloading": return "#3b82f6"
        case "queued": return "#64748b"
        case "canceled": return "#a855f7"
        default: return "#64748b"
        }
    }

    function statusText(status) {
        switch (status) {
        case "completed": return "Completado"
        case "error": return "Error"
        case "processing": return "Procesando"
        case "downloading": return "Descargando"
        case "queued": return "En cola"
        case "canceled": return "Cancelado"
        default: return status
        }
    }

    function canCancel(status) {
        return status === "queued" || status === "downloading" || status === "processing"
    }

    FolderDialog {
        id: folderDialog
        title: "Selecciona la carpeta de destino"

        onAccepted: {
            selectedFolder = folderDialog.selectedFolder.toString().replace("file://", "")
        }
    }

    Timer {
        id: toastTimer
        interval: 3200
        repeat: false
        onTriggered: toastBox.visible = false
    }

    ListModel {
        id: formatModel
    }

    ListModel {
        id: jobsModel
    }

    Connections {
        target: appBridge

        function onAnalysisStarted() {
            analyzeButton.enabled = false
            statusLabel.text = "Analizando URL..."
        }

        function onAnalysisFinished(payload) {
            analyzeButton.enabled = true
            mediaInfo = JSON.parse(payload)
            statusLabel.text = "Análisis completado"

            formatModel.clear()

            for (let i = 0; i < mediaInfo.formats.length; i++) {
                let f = mediaInfo.formats[i]
                formatModel.append({
                    label: f.label || f.resolution,
                    value: f.format_id
                })
            }

            if (formatModel.count > 0) {
                formatCombo.currentIndex = 0
            }
        }

        function onAnalysisError(message) {
            analyzeButton.enabled = true
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

    background: Rectangle {
        color: bgColor
    }

    ScrollView {
        id: pageScroll
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Item {
            width: pageScroll.availableWidth
            implicitHeight: contentColumn.implicitHeight + 48

            ColumnLayout {
                id: contentColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 24
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    radius: 22
                    color: panelColor
                    border.color: borderColor
                    border.width: 1
                    implicitHeight: headerLayout.implicitHeight + 32

                    ColumnLayout {
                        id: headerLayout
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            Rectangle {
                                Layout.preferredWidth: 48
                                Layout.preferredHeight: 48
                                radius: 14
                                color: "#1d4ed8"

                                Label {
                                    anchors.centerIn: parent
                                    text: "V"
                                    color: "white"
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
                                    font.pixelSize: 28
                                    font.bold: true
                                }

                                Label {
                                    text: "Aplicación desktop para descargar video y audio"
                                    color: mutedColor
                                    font.pixelSize: 14
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    radius: 22
                    color: panelColor
                    border.color: borderColor
                    border.width: 1
                    implicitHeight: searchCard.implicitHeight + 34

                    ColumnLayout {
                        id: searchCard
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 14

                        Label {
                            text: "Pega la URL del contenido"
                            color: textColor
                            font.pixelSize: 18
                            font.bold: true
                        }

                        TextField {
                            id: urlField
                            Layout.fillWidth: true
                            placeholderText: "YouTube, TikTok, Instagram, Facebook..."
                            selectByMouse: true

                            onAccepted: {
                                appBridge.analyzeUrl(text)
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Button {
                                id: analyzeButton
                                text: "Analizar"
                                onClicked: appBridge.analyzeUrl(urlField.text)
                            }

                            Button {
                                text: "Elegir carpeta"
                                onClicked: folderDialog.open()
                            }

                            Button {
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
                            radius: 12
                            color: panelSoftColor
                            border.color: borderColor
                            border.width: 1
                            implicitHeight: statusTextLabel.implicitHeight + 18

                            Label {
                                id: statusTextLabel
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.margins: 12
                                text: statusLabel.text
                                color: softTextColor
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
                    radius: 22
                    color: panelColor
                    border.color: borderColor
                    border.width: 1
                    implicitHeight: mediaCard.implicitHeight + 34

                    ColumnLayout {
                        id: mediaCard
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 16

                        Label {
                            text: "Contenido detectado"
                            color: textColor
                            font.pixelSize: 18
                            font.bold: true
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 18

                            Rectangle {
                                Layout.preferredWidth: 300
                                Layout.preferredHeight: 170
                                radius: 18
                                color: panelSoftColor
                                border.color: borderColor
                                border.width: 1
                                clip: true

                                Image {
                                    anchors.fill: parent
                                    fillMode: Image.PreserveAspectCrop
                                    source: mediaInfo && mediaInfo.thumbnail ? mediaInfo.thumbnail : ""
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
                                spacing: 10

                                Label {
                                    text: mediaInfo ? mediaInfo.title : ""
                                    color: textColor
                                    font.pixelSize: 22
                                    font.bold: true
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: mediaInfo ? ("Duración: " + mediaInfo.duration_text + "   |   Plataforma: " + mediaInfo.extractor) : ""
                                    color: mutedColor
                                    wrapMode: Text.Wrap
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: "Formato de video"
                                    color: textColor
                                    font.bold: true
                                }

                                ComboBox {
                                    id: formatCombo
                                    Layout.fillWidth: true
                                    model: formatModel
                                    textRole: "label"
                                    valueRole: "value"
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10

                                    Button {
                                        text: "Descargar video"
                                        enabled: mediaInfo !== null
                                        onClicked: {
                                            appBridge.downloadMedia(
                                                mediaInfo.webpage_url,
                                                selectedFolder,
                                                formatCombo.currentValue || "",
                                                false,
                                                "mp4",
                                                mediaInfo.title
                                            )
                                        }
                                    }

                                    Button {
                                        text: "Descargar audio MP3"
                                        enabled: mediaInfo !== null
                                        onClicked: {
                                            appBridge.downloadMedia(
                                                mediaInfo.webpage_url,
                                                selectedFolder,
                                                "",
                                                true,
                                                "mp3",
                                                mediaInfo.title
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    radius: 22
                    color: panelColor
                    border.color: borderColor
                    border.width: 1
                    implicitHeight: downloadsCard.implicitHeight + 34

                    ColumnLayout {
                        id: downloadsCard
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 14

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
                                text: jobsModel.count > 0 ? (jobsModel.count + " elemento(s)") : ""
                                color: mutedColor
                            }
                        }

                        Rectangle {
                            visible: jobsModel.count === 0
                            Layout.fillWidth: true
                            radius: 16
                            color: panelSoftColor
                            border.color: borderColor
                            border.width: 1
                            implicitHeight: emptyState.implicitHeight + 24

                            ColumnLayout {
                                id: emptyState
                                anchors.centerIn: parent
                                spacing: 6

                                Label {
                                    text: "Todavía no hay descargas"
                                    color: textColor
                                    font.pixelSize: 16
                                    font.bold: true
                                    horizontalAlignment: Text.AlignHCenter
                                }

                                Label {
                                    text: "Analiza una URL y añade una descarga para verla aquí."
                                    color: mutedColor
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                        }

                        ListView {
                            visible: jobsModel.count > 0
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.min(contentHeight, 460)
                            model: jobsModel
                            spacing: 12
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
                                radius: 18
                                color: panelSoftColor
                                border.color: borderColor
                                border.width: 1
                                implicitHeight: jobCard.implicitHeight + 24

                                ColumnLayout {
                                    id: jobCard
                                    anchors.fill: parent
                                    anchors.margins: 14
                                    spacing: 10

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 10

                                        Label {
                                            text: title
                                            color: textColor
                                            font.bold: true
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }

                                        Rectangle {
                                            radius: 999
                                            color: badgeColor(status)
                                            implicitWidth: badgeLabel.implicitWidth + 18
                                            implicitHeight: badgeLabel.implicitHeight + 8

                                            Label {
                                                id: badgeLabel
                                                anchors.centerIn: parent
                                                text: statusText(status)
                                                color: "white"
                                                font.bold: true
                                                font.pixelSize: 12
                                            }
                                        }
                                    }

                                    Label {
                                        text: message
                                        color: softTextColor
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

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12

                                        Label {
                                            text: percent >= 0 ? (percent.toFixed(1) + "%") : "Calculando..."
                                            color: mutedColor
                                        }

                                        Label {
                                            text: "Velocidad: " + speed_text
                                            color: mutedColor
                                        }

                                        Label {
                                            text: "ETA: " + eta_text
                                            color: mutedColor
                                        }

                                        Item {
                                            Layout.fillWidth: true
                                        }

                                        Label {
                                            text: bytes_text
                                            color: mutedColor
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 10

                                        Button {
                                            text: "Cancelar"
                                            visible: canCancel(status)
                                            onClicked: appBridge.cancelDownload(job_id)
                                        }

                                        Button {
                                            text: "Abrir carpeta"
                                            onClicked: appBridge.openFolder(folder)
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
        anchors.margins: 22
        radius: 14
        color: toastLevel === "error"
               ? "#7f1d1d"
               : toastLevel === "success"
                 ? "#14532d"
                 : "#1e3a8a"
        border.color: toastLevel === "error"
                      ? "#ef4444"
                      : toastLevel === "success"
                        ? "#22c55e"
                        : "#60a5fa"
        border.width: 1
        width: Math.min(420, toastText.implicitWidth + 34)
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