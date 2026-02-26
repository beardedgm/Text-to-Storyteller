class StorytellerApp {
    constructor() {
        this.jobId = null;
        this.pollInterval = null;
        this.startTime = null;
        this.totalChunks = 0;
        this.selectedFile = null;
        this.activeTab = 'upload';

        this.els = {
            tabs: document.querySelectorAll('.tab'),
            tabUpload: document.getElementById('tab-upload'),
            tabPaste: document.getElementById('tab-paste'),
            dropZone: document.getElementById('drop-zone'),
            fileInput: document.getElementById('file-input'),
            fileSelected: document.getElementById('file-selected'),
            fileName: document.getElementById('file-name'),
            clearFile: document.getElementById('clear-file'),
            textInput: document.getElementById('text-input'),
            voiceSelect: document.getElementById('voice-select'),
            speedSlider: document.getElementById('speed-slider'),
            speedValue: document.getElementById('speed-value'),
            pitchSlider: document.getElementById('pitch-slider'),
            pitchValue: document.getElementById('pitch-value'),
            btnGenerate: document.getElementById('btn-generate'),
            errorBanner: document.getElementById('error-banner'),
            errorMessage: document.getElementById('error-message'),
            clearError: document.getElementById('clear-error'),
            progressSection: document.getElementById('progress-section'),
            progressBar: document.getElementById('progress-bar'),
            progressChunks: document.getElementById('progress-chunks'),
            progressTime: document.getElementById('progress-time'),
            downloadSection: document.getElementById('download-section'),
            btnDownload: document.getElementById('btn-download'),
        };

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Tab switching
        this.els.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Drop zone
        const dz = this.els.dropZone;
        dz.addEventListener('click', () => this.els.fileInput.click());
        dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
        dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
        dz.addEventListener('drop', e => {
            e.preventDefault();
            dz.classList.remove('drag-over');
            if (e.dataTransfer.files.length) this.setFile(e.dataTransfer.files[0]);
        });

        this.els.fileInput.addEventListener('change', () => {
            if (this.els.fileInput.files.length) this.setFile(this.els.fileInput.files[0]);
        });

        this.els.clearFile.addEventListener('click', e => {
            e.stopPropagation();
            this.clearFile();
        });

        // Sliders
        this.els.speedSlider.addEventListener('input', () => {
            this.els.speedValue.textContent = this.els.speedSlider.value + 'x';
        });
        this.els.pitchSlider.addEventListener('input', () => {
            this.els.pitchValue.textContent = this.els.pitchSlider.value;
        });

        // Generate
        this.els.btnGenerate.addEventListener('click', () => this.submit());

        // Download
        this.els.btnDownload.addEventListener('click', () => {
            window.location.href = '/api/download/' + this.jobId;
        });

        // Clear error
        this.els.clearError.addEventListener('click', () => this.hideError());
    }

    switchTab(tab) {
        this.activeTab = tab;
        this.els.tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
        this.els.tabUpload.classList.toggle('active', tab === 'upload');
        this.els.tabPaste.classList.toggle('active', tab === 'paste');
    }

    setFile(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['md', 'txt', 'markdown'].includes(ext)) {
            this.showError('Please select a .md, .txt, or .markdown file');
            return;
        }
        this.selectedFile = file;
        this.els.fileName.textContent = file.name + ' (' + this.formatSize(file.size) + ')';
        this.els.fileSelected.hidden = false;
    }

    clearFile() {
        this.selectedFile = null;
        this.els.fileInput.value = '';
        this.els.fileSelected.hidden = true;
    }

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    showError(msg) {
        this.els.errorMessage.textContent = msg;
        this.els.errorBanner.hidden = false;
    }

    hideError() {
        this.els.errorBanner.hidden = true;
    }

    async submit() {
        this.hideError();
        this.els.downloadSection.hidden = true;
        this.els.progressSection.hidden = true;

        const formData = new FormData();

        if (this.activeTab === 'upload') {
            if (!this.selectedFile) {
                this.showError('Please select a file to upload');
                return;
            }
            formData.append('file', this.selectedFile);
        } else {
            const text = this.els.textInput.value.trim();
            if (!text) {
                this.showError('Please enter some text');
                return;
            }
            formData.append('text', text);
        }

        formData.append('voice_name', this.els.voiceSelect.value);
        formData.append('speaking_rate', this.els.speedSlider.value);
        formData.append('pitch', this.els.pitchSlider.value);

        this.els.btnGenerate.disabled = true;
        this.els.btnGenerate.textContent = 'Starting...';

        try {
            const resp = await fetch('/api/synthesize', {
                method: 'POST',
                body: formData,
            });
            const data = await resp.json();

            if (data.error) {
                this.showError(data.error);
                this.resetButton();
                return;
            }

            this.jobId = data.job_id;
            this.totalChunks = data.total_chunks;
            this.startTime = Date.now();

            this.els.progressSection.hidden = false;
            this.els.progressChunks.textContent = '0 / ' + this.totalChunks;
            this.els.progressBar.style.width = '0%';
            this.els.progressTime.textContent = 'Estimating...';

            this.pollInterval = setInterval(() => this.checkStatus(), 1000);

        } catch (err) {
            this.showError('Failed to connect to server: ' + err.message);
            this.resetButton();
        }
    }

    async checkStatus() {
        try {
            const resp = await fetch('/api/status/' + this.jobId);
            const data = await resp.json();

            if (data.error && data.status === 'error') {
                clearInterval(this.pollInterval);
                this.showError('Generation failed: ' + data.error);
                this.els.progressSection.hidden = true;
                this.resetButton();
                return;
            }

            const completed = data.completed_chunks;
            const total = data.total_chunks;
            const pct = total > 0 ? (completed / total) * 100 : 0;

            this.els.progressBar.style.width = pct + '%';
            this.els.progressChunks.textContent = completed + ' / ' + total;

            if (completed > 0) {
                const elapsed = (Date.now() - this.startTime) / 1000;
                const avgPerChunk = elapsed / completed;
                const remaining = avgPerChunk * (total - completed);
                this.els.progressTime.textContent = this.formatTime(remaining) + ' remaining';
            }

            if (data.status === 'complete') {
                clearInterval(this.pollInterval);
                this.els.progressSection.hidden = true;
                this.els.downloadSection.hidden = false;
                this.resetButton();
            }

        } catch (err) {
            // Network hiccup; keep polling
        }
    }

    formatTime(seconds) {
        if (seconds < 60) return Math.ceil(seconds) + 's';
        const mins = Math.floor(seconds / 60);
        const secs = Math.ceil(seconds % 60);
        return mins + 'm ' + secs + 's';
    }

    resetButton() {
        this.els.btnGenerate.disabled = false;
        this.els.btnGenerate.textContent = 'Generate Audio';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new StorytellerApp();
});
