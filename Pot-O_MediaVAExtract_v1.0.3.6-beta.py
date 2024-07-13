import json
import os
import sys
import time
import subprocess

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton

import assets_rc  # Import the compiled resource module
from PotO_UI import Ui_MainWindow
from AboutPotOui import Ui_Dialog

mkvList = []
webmList = []

class MediaExtract(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Set fixed size to prevent resizing
        self.setFixedSize(546, 471)  # Set your desired width and height

        # Create a status bar
        self.statusBar = self.statusBar()

        self.ui.sourceButton.clicked.connect(self.sourceButtonClicked)
        self.ui.targetButton.clicked.connect(self.targetButtonClicked)
        self.ui.startProcess.clicked.connect(self.startProcessClicked)
        self.ui.abortProcess.clicked.connect(self.abortProcessClicked)

        # Create File menu and add actions
        file_menu = self.menuBar().addMenu("&File")

        # Create actions for File menu
        open_action = QtWidgets.QAction("&Open", self)
        open_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
        file_menu.addAction(open_action)
        open_action.triggered.connect(self.openFile)

        exit_action = QtWidgets.QAction("&Exit", self)
        exit_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton))
        file_menu.addAction(exit_action)
        exit_action.triggered.connect(QtWidgets.qApp.quit)

        # Create a new menu action for setting code page
        set_code_page_action = QtWidgets.QAction("&Set Code Page", self)
        self.menuBar().addAction(set_code_page_action)
        set_code_page_action.triggered.connect(self.setUtf8CodePage)

        help_menu = self.menuBar().addMenu("&Help")

        about_action = QtWidgets.QAction("&About", self)
        about_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation))
        help_menu.addAction(about_action)
        about_action.triggered.connect(self.show_about_dialog)

        # Set the initial status bar message
        self.updateStatusBar([])  # Pass an empty list as no files are selected initially

        # Check and set UTF-8 code page
        self.check_and_set_utf8_code_page()

        self.show()

    def openFile(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.ReadOnly
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Source Files", "", "Media Files (*.mp4);;MKV Files (*.mkv);;All Files (*)", options=options)

        # Decode file names using utf-8 to handle non-ASCII characters like Japanese
        file_paths = [path.encode('utf-8').decode('utf-8') for path in file_paths]

        self.ui.sourcePath.setText("\n".join(file_paths))

        # Get the first file name from the list (assuming at least one file is selected)
        self.updateStatusBar(file_paths)

    def sourceButtonClicked(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.ReadOnly
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Source Files", "", "Media Files (*.mp4);;MKV Files (*.mkv);;All Files (*)", options=options)

        # Decode file names using utf-8 to handle non-ASCII characters like Japanese
        file_paths = [path.encode('utf-8').decode('utf-8') for path in file_paths]

        self.ui.sourcePath.setText("\n".join(file_paths))

        # Get the first file name from the list (assuming at least one file is selected)
        self.updateStatusBar(file_paths)

    def targetButtonClicked(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.ShowDirsOnly
        target_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Target Folder", "", options=options)

        # Decode target path using utf-8 to handle non-ASCII characters like Japanese
        target_path = target_path.encode('utf-8').decode('utf-8')

        self.ui.targetPath.setText(target_path)

    def startProcessClicked(self):
        # Get the input file paths and output directory
        input_paths = self.ui.sourcePath.text().strip().split("\n")
        output_dir = self.ui.targetPath.text().strip()

        # Check if there are no input files
        if not any(input_paths):
            self.displayInConsole("No input file provided. Please select input file(s) to process.")
            return

        # Disable the startProcessButton
        self.ui.startProcess.setEnabled(False)

        self.displayInConsole("Starting processing...")

        for input_file in input_paths:
            if not input_file:
                continue  # Skip empty input file paths

            base_name, ext = os.path.splitext(os.path.basename(input_file))

            if ext.lower() == ".mp4":
                self.displayInConsole(f"Processing Media: {input_file}")
                self.extract_audio_and_video(input_file, output_dir)
            elif ext.lower() in (".mkv", ".webm"):
                self.displayInConsole(f"Processing MKV/WebM: {input_file}")
                self.runTracks(input_file, output_dir)
            else:
                self.displayInConsole(f"Unsupported file format: {input_file}")

        # Enable the startProcessButton after processing is complete
        self.displayInConsole("Processing complete.")

        # After the process has completed:
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle("Process Completed")
        msgBox.setText("The process has completed successfully.")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()

        # Enable the startProcess button
        self.ui.startProcess.setEnabled(True)

    def abortProcessClicked(self):
        self.ui.startProcess.setEnabled(True)
        sys.exit(1)

    def displayInConsole(self, text):
        sentences = text.split('.')
        for sentence in sentences:
            words = sentence.split()
            for word in words:
                self.ui.processWindow.moveCursor(QtGui.QTextCursor.End)
                self.ui.processWindow.insertPlainText(word + ' ')
                QtGui.QGuiApplication.processEvents()
            self.ui.processWindow.insertPlainText('. ')
            QtGui.QGuiApplication.processEvents()

    def executeCommand(self, input_file, output_dir):
        base_name = os.path.basename(input_file)
        name, ext = os.path.splitext(base_name)

        if ext.lower() == ".mp4":
            self.extract_audio_and_video(input_file, output_dir)
        elif ext.lower() == ".mkv":
            self.extract_all_from_mkv(input_file, output_dir)
        else:
            print("Unsupported file format.")

    def extract_audio_and_video(self, input_file, output_dir):
        base_name = os.path.basename(input_file)
        name, _ = os.path.splitext(base_name)

        ffprobe_command_audio = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", input_file]
        audio_codec = subprocess.check_output(ffprobe_command_audio, text=True, stderr=subprocess.STDOUT).strip()

        ffprobe_command_video = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", input_file]
        video_codec = subprocess.check_output(ffprobe_command_video, text=True, stderr=subprocess.STDOUT).strip()

        audio_output = os.path.join(output_dir, f"{name}_audio.{audio_codec}")
        video_output = os.path.join(output_dir, f"{name}_video.{video_codec}")

        audio_command = ["ffmpeg", "-i", input_file, "-vn", "-acodec", "copy", audio_output]
        video_command = ["ffmpeg", "-i", input_file, "-an", "-vcodec", "copy", video_output]

        self.executeFFmpegCommand(audio_command, f"Audio extracted to: {audio_output}")
        self.executeFFmpegCommand(video_command, f"Video extracted to: {video_output}")

    def get_output(self, mediaFile):
        global jsonData

        mkvmerge_JSON = subprocess.check_output(
            [
                'mkvmerge',
                '--identify',
                '--identification-format',
                'json',
                os.path.abspath(mediaFile),
            ],
            stderr=subprocess.DEVNULL
        )
        jsonData = json.loads(mkvmerge_JSON)

        return jsonData

    def get_tracks(self, mediaFile):
        self.get_output(mediaFile)
        global id
        global language
        global language_ietf
        global title
        global codec_id
        global codec
        global track_type

        id = jsonData.get('tracks')[int(i)].get('id')
        language = jsonData.get('tracks')[int(i)].get('properties').get('language')
        language_ietf = jsonData.get('tracks')[int(i)].get('properties').get('language_ietf')
        title = jsonData.get('tracks')[int(i)].get('properties').get('track_name')
        codec_id = jsonData.get('tracks')[int(i)].get('properties').get('codec_id')
        codec = jsonData.get('tracks')[int(i)].get('codec')
        track_type = jsonData.get('tracks')[int(i)].get('type')

    def get_attachments(self, mediaFile):
        self.get_output(mediaFile)
        global attach_id
        global attach_type
        global attach_desc
        global attach_name
        global attach_uid

        attach_id = jsonData.get('attachments')[int(i)].get('id')
        attach_type = jsonData.get('attachments')[int(i)].get('content_type')
        attach_desc = jsonData.get('attachments')[int(i)].get('description')
        attach_name = jsonData.get('attachments')[int(i)].get('file_name')
        attach_uid = jsonData.get('attachments')[int(i)].get('properties').get('uid')

    def processFile(self, mediaFile):
        global extractName

        if track_type == 'video':
            pixel_dimensions = jsonData.get('tracks')[int(i)].get('properties').get('pixel_dimensions')
            extractName = f'TrackID_{id}_[{track_type}]_[{pixel_dimensions}]_[{language}]'
        elif track_type == 'audio':
            audio_channels = jsonData.get('tracks')[int(i)].get('properties').get('audio_channels')
            audio_sampling_frequency = jsonData.get('tracks')[int(i)].get('properties').get('audio_sampling_frequency')
            extractName = f'TrackID_{id}_[{track_type}]_[{audio_channels}CH]_[{audio_sampling_frequency / 1000}kHz]_[{language}]'
        elif track_type == "subtitles":
            extractName = f'TrackID_{id}_[{track_type}]_[{language}]'

        if "AVC" in codec_id:
            extractName = extractName + ".264"
        elif "HEVC" in codec_id:
            extractName = extractName + ".hevc"
        elif "V_VP8" in codec_id:
            extractName = extractName + ".ivf"
        elif "V_VP9" in codec_id:
            extractName = extractName + ".ivf"
        elif "V_AV1" in codec_id:
            extractName = extractName + ".ivf"
        elif "V_MPEG1" in codec_id:
            extractName = extractName + ".mpg"
        elif "V_MPEG2" in codec_id:
            extractName = extractName + ".mpg"
        elif "V_REAL" in codec_id:
            extractName = extractName + ".rm"
        elif "V_THEORA" in codec_id:
            extractName = extractName + ".ogg"
        elif "V_MS/VFW/FOURCC" in codec_id:
            extractName = extractName + ".avi"
        elif "AAC" in codec_id:
            extractName = extractName + ".aac"
        elif "A_AC3" in codec_id:
            extractName = extractName + ".ac3"
        elif "A_EAC3" in codec_id:
            extractName = extractName + ".eac3"
        elif "ALAC" in codec_id:
            extractName = extractName + ".caf"
        elif "DTS" in codec_id:
            extractName = extractName + ".dts"
        elif "FLAC" in codec_id:
            extractName = extractName + ".flac"
        elif "MPEG/L2" in codec_id:
            extractName = extractName + ".mp2"
        elif "MPEG/L3" in codec_id:
            extractName = extractName + ".mp3"
        elif "OPUS" in codec_id:
            extractName = extractName + ".ogg"
        elif "PCM" in codec_id:
            extractName = extractName + ".wav"
        elif "REAL" in codec_id:
            extractName = extractName + ".ra"
        elif "TRUEHD" in codec_id:
            extractName = extractName + ".thd"
        elif "MLP" in codec_id:
            extractName = extractName + ".mlp"
        elif "TTA1" in codec_id:
            extractName = extractName + ".tta"
        elif "VORBIS" in codec_id:
            extractName = extractName + ".ogg"
        elif "WAVPACK4" in codec_id:
            extractName = extractName + ".wv"
        elif "PGS" in codec_id:
            extractName = extractName + ".sup"
        elif "ASS" in codec_id:
            extractName = extractName + ".ass"
        elif "SSA" in codec_id:
            extractName = extractName + ".ssa"
        elif "UTF8" in codec_id:
            extractName = extractName + ".srt"
        elif "ASCII" in codec_id:
            extractName = extractName + ".srt"
        elif "VOBSUB" in codec_id:
            extractName = extractName + ".sub"
        elif "S_KATE" in codec_id:
            extractName = extractName + ".ogg"
        elif "USF" in codec_id:
            extractName = extractName + ".usf"
        elif "WEBVTT" in codec_id:
            extractName = extractName + ".vtt"
        elif track_type == 'fonts':
            extractName = "ttf"  # Common extension for font files

        return extractName

    def extract_all_from_mkv(self, input_file, output_dir):
        base_name = os.path.basename(input_file)
        name, _ = os.path.splitext(base_name)

        # Create directories for tracks and attachments
        output_tracks_dir = os.path.join(output_dir, f"{name}_tracks")
        os.makedirs(output_tracks_dir, exist_ok=True)

        # Extract all tracks and attachments from MKV
        mkvextract_path = os.path.join(os.path.dirname(__file__), "mkvextract.exe")

        # Get the list of tracks in the MKV file
        mkvinfo_command = ["mkvinfo", input_file]
        mkvinfo_output = subprocess.check_output(mkvinfo_command).decode("utf-8")
        track_ids = [line.split()[2] for line in mkvinfo_output.split("\n") if "Track ID" in line]

        # Extract all tracks
        for track_id in track_ids:
            output_file = os.path.join(output_tracks_dir, f"{name}_track_{track_id}".replace('[', '_').replace(']', '_'))
            mkvextract_command = [mkvextract_path, "tracks", input_file, f"{track_id}:{output_file}"]
            try:
                subprocess.run(mkvextract_command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to extract track {track_id}: {e}")

        # Extract attachments
        attachments_output_dir = os.path.join(output_dir, f"{name}_attachments")
        mkvextract_attachments_command = [mkvextract_path, "attachments", input_file, attachments_output_dir]
        try:
            subprocess.run(mkvextract_attachments_command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to extract attachments: {e}")

        print(f"All tracks and attachments extracted to: {output_dir}")

    def executeFFmpegCommand(self, command, success_message):
        try:
            popen_kwargs = self._popen_kwargs(hide_console=True)

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',  # Specify the encoding for subprocess stdout
                **popen_kwargs  # Include additional kwargs from _popen_kwargs
            )
            process.wait()
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.displayInConsole(line.strip())

            self.displayInConsole(success_message)
        except subprocess.CalledProcessError as e:
            self.displayInConsole(f"Extraction failed: {e}")

    def runTracks(self, mediaFile, output_dir):
        global i

        commandList = []

        # Get output information
        self.get_output(mediaFile)
        trackCount = len(jsonData['tracks'])

        # Create the output directory for tracks
        output_tracks_dir = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(mediaFile))[0]}_tracks")
        os.makedirs(output_tracks_dir, exist_ok=True)

        for i in range(trackCount):
            self.get_tracks(mediaFile)
            extractName = self.processFile(mediaFile)
            extractPath = os.path.join(output_tracks_dir, f"{extractName}")
            extractParam = f'{id}:"{extractPath}"'
            commandList.append(extractParam)

        extractParam = ' '.join(commandList)
        command = f'mkvextract "{mediaFile}" tracks {extractParam}'
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(process.stdout.decode())

    def _popen_kwargs(prevent_sigint=False, hide_console=False):
        startupinfo = None
        preexec_fn = None
        creationflags = 0

        if sys.platform.startswith("win"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            if hide_console:
                # Hide the console window
                creationflags |= subprocess.CREATE_NO_WINDOW

        if prevent_sigint:
            if sys.platform.startswith("win"):
                # Prevent the child process from receiving CTRL+C signal
                creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            else:
                preexec_fn = os.setpgrp  # Prevent the child process from receiving SIGINT signal

        return {
            "startupinfo": startupinfo,
            "creationflags": creationflags,
            "preexec_fn": preexec_fn,
        }
    
    def check_and_set_utf8_code_page(self):
        try:
            subprocess.run(['chcp', '65001'], check=True, shell=True)
            print("Code page set to UTF-8")
        except subprocess.CalledProcessError as e:
            self.displayInConsole(f"Error setting code page: {e}. Please set the code page to UTF-8 manually by clicking the menu 'Set Code Page' button if the file contain non roman alphabets (e.g. Japanese or Chinese).")

    def setUtf8CodePage(self):
        try:
            subprocess.run(['chcp', '65001'], check=True, shell=True)
            print("Code page set to UTF-8")
        except subprocess.CalledProcessError as e:
            self.displayInConsole(f"Error setting code page: {e}. Please set the code page to UTF-8 manually by clicking the menu 'Set Code Page' button if the file contain non roman alphabets (e.g. Japanese or Chinese).")

    def updateStatusBar(self, file_paths):
        file_count = len(file_paths)

        if file_count == 1:
            selected_file = os.path.basename(file_paths[0])
            self.statusBar.showMessage(f"Selected File: {selected_file}")
        elif file_count > 1:
            self.statusBar.showMessage(f"Open {file_count} files to be processed")
        else:
            self.statusBar.showMessage("No file selected")

    def show_about_dialog(self):
        about_dialog = QtWidgets.QDialog(self)
        ui = Ui_Dialog()
        ui.setupUi(about_dialog)

        # Connect OK button's accepted signal to the dialog's accept slot
        ui.buttonBox.accepted.connect(about_dialog.accept)

        about_dialog.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MediaExtract()
    main_window.show()
    sys.exit(app.exec_())