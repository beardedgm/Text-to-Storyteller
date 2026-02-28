class StorytellerApp {
    constructor() {
        this.jobId = null;
        this.pollInterval = null;
        this.startTime = null;
        this.totalChunks = 0;
        this.selectedFile = null;
        this.activeTab = 'upload';

        // Voice data (populated by loadVoices)
        this.voiceData = [];
        this.categories = [];
        this.activeCategory = 'all';
        this.defaultVoice = '';

        // Presets & source texts
        this.presets = [];
        this.sourceTexts = [];
        this.loadedSourceTextId = null;

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
            voiceCategoryFilters: document.getElementById('voice-category-filters'),
            voiceCount: document.getElementById('voice-count'),
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
            resultSection: document.getElementById('result-section'),
            audioPlayer: document.getElementById('audio-player'),
            // New elements
            presetSelect: document.getElementById('preset-select'),
            btnSavePreset: document.getElementById('btn-save-preset'),
            btnDeletePreset: document.getElementById('btn-delete-preset'),
            audioTitle: document.getElementById('audio-title'),
            saveTextCheck: document.getElementById('save-text-check'),
            saveTextTitle: document.getElementById('save-text-title'),
            sourceTextPicker: document.getElementById('source-text-picker'),
            sourceTextSelect: document.getElementById('source-text-select'),
        };

        this.setupEventListeners();
        this.loadVoices();
        this.loadPresets();
        this.loadSourceTexts();
        this.checkUrlParams();
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
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        });
        this.els.pitchSlider.addEventListener('input', () => {
            this.els.pitchValue.textContent = this.els.pitchSlider.value;
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        });
        this.els.voiceSelect.addEventListener('change', () => {
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        });

        // Generate
        this.els.btnGenerate.addEventListener('click', () => this.submit());

        // Clear error
        this.els.clearError.addEventListener('click', () => this.hideError());

        // Presets
        this.els.presetSelect.addEventListener('change', () => this.applyPreset());
        this.els.btnSavePreset.addEventListener('click', () => this.savePreset());
        this.els.btnDeletePreset.addEventListener('click', () => this.deletePreset());

        // Save text checkbox
        this.els.saveTextCheck.addEventListener('change', () => {
            this.els.saveTextTitle.hidden = !this.els.saveTextCheck.checked;
        });

        // Source text picker
        this.els.sourceTextSelect.addEventListener('change', () => this.loadSourceText());
    }

    // ── Voice loading & filtering ──────────────────────────────

    async loadVoices() {
        try {
            const resp = await fetch('/api/voices');
            const data = await resp.json();
            this.voiceData = data.voices;
            this.categories = data.categories;
            this.defaultVoice = data.default;
            this.renderCategoryChips();
            this.renderVoiceOptions('all');
        } catch (err) {
            console.error('Failed to load voices:', err);
        }
    }

    renderCategoryChips() {
        const container = this.els.voiceCategoryFilters;

        this.categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.className = 'category-chip';
            btn.dataset.category = cat.id;
            btn.textContent = cat.label;
            btn.title = cat.description;
            container.appendChild(btn);
        });

        container.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                container.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.activeCategory = chip.dataset.category;
                this.renderVoiceOptions(this.activeCategory);
            });
        });
    }

    renderVoiceOptions(category) {
        const select = this.els.voiceSelect;
        const previousValue = select.value;
        select.innerHTML = '';

        const filtered = category === 'all'
            ? this.voiceData
            : this.voiceData.filter(v => v.category === category);

        const showCategory = category === 'all';

        filtered.forEach(voice => {
            const opt = document.createElement('option');
            opt.value = voice.api_name;
            const genderLabel = voice.gender === 'M' ? 'M' : 'F';
            if (showCategory) {
                const catDef = this.categories.find(c => c.id === voice.category);
                const catLabel = catDef ? catDef.label : '';
                opt.textContent = voice.display_name + ' (' + genderLabel + ') \u2014 ' + catLabel;
            } else {
                opt.textContent = voice.display_name + ' (' + genderLabel + ')';
            }
            select.appendChild(opt);
        });

        const previousStillVisible = filtered.some(v => v.api_name === previousValue);
        if (previousStillVisible) {
            select.value = previousValue;
        } else {
            const defaultInList = filtered.some(v => v.api_name === this.defaultVoice);
            select.value = defaultInList ? this.defaultVoice : (filtered[0]?.api_name || '');
        }

        this.els.voiceCount.textContent = filtered.length + ' voice' + (filtered.length !== 1 ? 's' : '');
    }

    // ── Presets ────────────────────────────────────────────────

    async loadPresets() {
        try {
            const resp = await fetch('/api/presets');
            const data = await resp.json();
            this.presets = data.presets || [];
            this.renderPresetOptions();
        } catch (err) {
            console.error('Failed to load presets:', err);
        }
    }

    renderPresetOptions() {
        const select = this.els.presetSelect;
        select.innerHTML = '<option value="">Custom settings</option>';
        this.presets.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            select.appendChild(opt);
        });
    }

    applyPreset() {
        const presetId = this.els.presetSelect.value;
        if (!presetId) {
            this.els.btnDeletePreset.hidden = true;
            return;
        }

        const preset = this.presets.find(p => p.id === presetId);
        if (!preset) return;

        // Apply voice
        this.els.voiceSelect.value = preset.voice_name;
        if (!this.els.voiceSelect.value) {
            // Voice might be filtered out — switch to "All" category
            this.activeCategory = 'all';
            this.els.voiceCategoryFilters.querySelectorAll('.category-chip')
                .forEach(c => c.classList.toggle('active', c.dataset.category === 'all'));
            this.renderVoiceOptions('all');
            this.els.voiceSelect.value = preset.voice_name;
        }

        // Apply speed & pitch
        this.els.speedSlider.value = preset.speaking_rate;
        this.els.speedValue.textContent = preset.speaking_rate + 'x';
        this.els.pitchSlider.value = preset.pitch;
        this.els.pitchValue.textContent = preset.pitch;

        this.els.btnDeletePreset.hidden = false;
    }

    async savePreset() {
        const name = prompt('Preset name:');
        if (!name || !name.trim()) return;

        try {
            const resp = await fetch('/api/presets', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name.trim(),
                    voice_name: this.els.voiceSelect.value,
                    speaking_rate: parseFloat(this.els.speedSlider.value),
                    pitch: parseFloat(this.els.pitchSlider.value),
                }),
            });
            const data = await resp.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.presets.push(data.preset);
            this.renderPresetOptions();
            this.els.presetSelect.value = data.preset.id;
            this.els.btnDeletePreset.hidden = false;
        } catch (err) {
            this.showError('Failed to save preset');
        }
    }

    async deletePreset() {
        const presetId = this.els.presetSelect.value;
        if (!presetId) return;
        if (!confirm('Delete this preset?')) return;

        try {
            await fetch('/api/presets/' + presetId, {method: 'DELETE'});
            this.presets = this.presets.filter(p => p.id !== presetId);
            this.renderPresetOptions();
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        } catch (err) {
            this.showError('Failed to delete preset');
        }
    }

    // ── Source Texts ───────────────────────────────────────────

    async loadSourceTexts() {
        try {
            const resp = await fetch('/api/texts');
            const data = await resp.json();
            this.sourceTexts = data.texts || [];
            this.renderSourceTextOptions();
        } catch (err) {
            console.error('Failed to load source texts:', err);
        }
    }

    renderSourceTextOptions() {
        const select = this.els.sourceTextSelect;
        select.innerHTML = '<option value="">-- Load from My Texts --</option>';

        if (this.sourceTexts.length === 0) {
            this.els.sourceTextPicker.hidden = true;
            return;
        }

        this.els.sourceTextPicker.hidden = false;
        this.sourceTexts.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.title + ' (' + t.char_count.toLocaleString() + ' chars)';
            select.appendChild(opt);
        });
    }

    async loadSourceText() {
        const textId = this.els.sourceTextSelect.value;
        if (!textId) {
            this.loadedSourceTextId = null;
            return;
        }

        try {
            const resp = await fetch('/api/texts/' + textId);
            const data = await resp.json();
            if (data.text) {
                this.els.textInput.value = data.text.content;
                this.loadedSourceTextId = textId;
                // Switch to paste tab
                this.switchTab('paste');
                // Pre-fill audio title from text title
                if (!this.els.audioTitle.value) {
                    this.els.audioTitle.value = data.text.title;
                }
            }
        } catch (err) {
            this.showError('Failed to load text');
        }
    }

    checkUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const loadTextId = params.get('load_text');
        if (loadTextId) {
            // Will be loaded once source texts are fetched
            this.pendingLoadTextId = loadTextId;
            const origRender = this.renderSourceTextOptions.bind(this);
            this.renderSourceTextOptions = () => {
                origRender();
                if (this.pendingLoadTextId) {
                    this.els.sourceTextSelect.value = this.pendingLoadTextId;
                    this.loadSourceText();
                    this.pendingLoadTextId = null;
                    this.renderSourceTextOptions = origRender;
                }
            };
        }
    }

    // ── Core app logic ─────────────────────────────────────────

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
        // Use filename (without extension) as default audio title
        if (!this.els.audioTitle.value) {
            this.els.audioTitle.value = file.name.replace(/\.[^.]+$/, '');
        }
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
        this.els.resultSection.hidden = true;
        this.els.progressSection.hidden = true;
        this.els.audioPlayer.pause();
        this.els.audioPlayer.removeAttribute('src');
        this.els.audioPlayer.load();

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

        // Audio title
        const audioTitle = this.els.audioTitle.value.trim() || 'Untitled';
        formData.append('audio_title', audioTitle);

        // Save text option
        if (this.els.saveTextCheck.checked) {
            formData.append('save_text', '1');
            formData.append('text_title', this.els.saveTextTitle.value.trim() || audioTitle);
        }

        // Link to existing source text
        if (this.loadedSourceTextId) {
            formData.append('source_text_id', this.loadedSourceTextId);
        }

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
                this.els.resultSection.hidden = false;
                this.els.audioPlayer.src = '/api/stream/' + this.jobId;
                this.els.audioPlayer.load();
                this.resetButton();

                // Refresh source texts list in case text was saved
                if (this.els.saveTextCheck.checked) {
                    this.loadSourceTexts();
                    this.els.saveTextCheck.checked = false;
                    this.els.saveTextTitle.hidden = true;
                }
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
