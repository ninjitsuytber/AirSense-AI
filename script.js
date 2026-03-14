const introSection = document.getElementById('intro-section');
const output = document.getElementById('output');
const commandInput = document.getElementById('command-input');
const cursor = document.getElementById('cursor');
const inputLeft = document.getElementById('input-left');
const inputRight = document.getElementById('input-right');

const bannerText = `█████╗ ██╗██████╗ ███████╗███████╗███╗   ██╗███████╗███████╗   █████╗ ██╗
██╔══██╗██║██╔══██╗██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝  ██╔══██╗██║
███████║██║██████╔╝███████╗█████╗  ██╔██╗ ██║███████╗█████╗    ███████║██║
██╔══██║██║██╔══██╗╚════██║██╔══╝  ██║╚██╗██║╚════██║██╔══╝    ██╔══██║██║
██║  ██║██║██║  ██║███████║███████╗██║ ╚████║███████║███████╗  ██║  ██║██║
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝  ╚═╝  ╚═╝╚═╝`;

const subBannerText = "Developed by <a href='https://stephensii.netlify.app/' target='_blank' class='btn-link'>Stephen Sii</a> from <a href='https://lattonlab.netlify.app/' target='_blank' class='btn-link'>Latton Lab</a>";


let currentMode = 'normal';
let geminiKey = localStorage.getItem('gemini_api_key') || '';


const introText = "Welcome to the AirSense AI interactive terminal. Type 'help' for a list of available commands.";

const commands = {
    help: "Available commands:\n  airsense - Launch the AirSense AI Analysis Tool\n  about   - Display information about this site\n  clear   - Clear the terminal console\n  date    - Show current system date\n  echo    - Print given text",
    about: "This is a AI powered terminal-based website.\nBuilt by <a href='https://stephensii.netlify.app/' target='_blank' class='btn-link'>Stephen Sii</a> from <a href='https://lattonlab.netlify.app/' target='_blank' class='btn-link'>Latton Lab</a> using HTML, CSS, Vanilla JavaScript and Python.\nEnjoy the tool!",

    date: () => new Date().toString(),
};

function printBanner() {
    const bannerDiv = document.createElement('div');
    bannerDiv.className = 'item banner';
    bannerDiv.textContent = bannerText;
    introSection.appendChild(bannerDiv);

    const subBannerDiv = document.createElement('div');
    subBannerDiv.className = 'item sub-banner';
    subBannerDiv.innerHTML = subBannerText;
    introSection.appendChild(subBannerDiv);
}

async function typeText(text, delay = 15) {
    const div = document.createElement('div');
    div.className = 'item';
    introSection.appendChild(div);

    for (let char of text) {
        div.textContent += char;
        scrollToBottom();
        await new Promise(r => setTimeout(r, delay));
    }
}

function printLine(text, isHtml = false) {
    const div = document.createElement('div');
    div.className = 'item';
    if (isHtml) {
        div.innerHTML = text;
    } else {
        div.textContent = text;
    }
    output.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    const terminalContent = document.querySelector('.terminal-content');
    terminalContent.scrollTop = terminalContent.scrollHeight;
}

document.addEventListener('click', () => {
    commandInput.focus();
});

function updateInput() {
    const val = commandInput.value;
    const pos = commandInput.selectionStart;

    inputLeft.textContent = val.substring(0, pos);

    if (pos < val.length) {
        const cursorChar = val.substring(pos, pos + 1);
        cursor.textContent = cursorChar;
        cursor.style.backgroundColor = 'var(--text-color)';
        cursor.style.color = 'var(--bg-color)';
        inputRight.textContent = val.substring(pos + 1);
    } else {
        cursor.textContent = '█';
        cursor.style.backgroundColor = 'transparent';
        cursor.style.color = 'var(--text-color)';
        inputRight.textContent = '';
    }

    const placeholder = document.getElementById('placeholder-text');
    if (placeholder) {
        if (val.length === 0) {
            placeholder.style.display = 'block';
            const targetText = currentMode === 'awaiting_key'
                ? 'Enter your API key here'
                : "Type 'help' for a list of available commands or type 'airsense' to start the AI Analyzer Tool";

            if (placeholder.getAttribute('data-target') !== targetText) {
                placeholder.setAttribute('data-target', targetText);
                typePlaceholder(placeholder, targetText);
            }
        } else {
            placeholder.style.display = 'none';
            placeholder.removeAttribute('data-target');
        }
    }
}

let placeholderInterval = null;
function typePlaceholder(element, text) {
    if (placeholderInterval) clearInterval(placeholderInterval);
    element.textContent = '';
    let i = 0;
    placeholderInterval = setInterval(() => {
        if (i < text.length) {
            element.textContent += text[i];
            i++;
        } else {
            clearInterval(placeholderInterval);
            placeholderInterval = null;
        }
    }, 5);
}

['input', 'keydown', 'click'].forEach(event => {
    commandInput.addEventListener(event, () => setTimeout(updateInput, 0));
});

commandInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        const cmdText = this.value.trim();


        output.innerHTML = '';
        const currentPrompt = document.querySelector('.prompt').textContent;
        const displayValue = commandInput.type === 'password' ? '*'.repeat(this.value.length) : this.value;
        printLine(`<span class="prompt">${currentPrompt}</span> ${displayValue}`, true);

        if (cmdText) {
            handleCommand(cmdText);
        }

        this.value = '';
        updateInput();
    }
});

function handleCommand(cmdText) {
    if (currentMode === 'awaiting_key') {
        geminiKey = cmdText;
        localStorage.setItem('gemini_api_key', geminiKey);
        currentMode = 'normal';
        commandInput.type = 'text';
        document.querySelector('.prompt').textContent = 'Visitor@AirSense-AI:~$';

        const placeholder = document.getElementById('placeholder-text');
        const targetText = "Type 'help' for a list of available commands or type 'airsense' to start the AI Analyzer Tool";
        placeholder.setAttribute('data-target', targetText);
        typePlaceholder(placeholder, targetText);

        if (commandInput.value.length > 0) {
            placeholder.style.display = 'none';
        } else {
            placeholder.style.display = 'block';
        }

        printLine("API Key saved securely (in localStorage).");
        triggerAirSenseUpload();
        return;
    }


    const args = cmdText.split(' ');
    const cmd = args[0].toLowerCase();

    if (cmd === 'clear') {
        output.innerHTML = '';
        setTimeout(updateInput, 0); // Trigger placeholder recalculation
        return;
    }

    if (cmd === 'echo') {
        printLine(args.slice(1).join(' '));
        return;
    }

    if (cmd === 'airsense') {
        if (geminiKey) {
            triggerAirSenseUpload();
        } else {
            startAirSenseWizard();
        }
        return;
    }


    if (commands[cmd]) {
        const response = typeof commands[cmd] === 'function' ? commands[cmd]() : commands[cmd];
        printLine(response, cmd === 'about');
    } else {

        printLine(`bash: ${cmd}: command not found`);
    }
}

function startAirSenseWizard() {
    printLine("Initializing AirSense AI Program...", true);
    printLine("The AirSense Backend requires a Google Gemini API Key to perform Data Analysis.");
    printLine("You can get one for free at <a href='https://aistudio.google.com/app/apikey' target='_blank' class='api-link'>Google AI Studio</a>.", true);
    printLine("");
    printLine("Please paste your Gemini API Key below:");
    currentMode = 'awaiting_key';
    commandInput.type = 'password';
    document.querySelector('.prompt').textContent = '>';
    const placeholderText = 'Enter your API key here';
    document.getElementById('placeholder-text').setAttribute('data-target', placeholderText);
    typePlaceholder(document.getElementById('placeholder-text'), placeholderText);
    updateInput();
}

function triggerAirSenseUpload() {
    printLine("Please choose an action:", true);

    const btnContainer = document.createElement('div');
    btnContainer.className = 'item';
    btnContainer.style.marginBottom = '15px';
    btnContainer.style.marginTop = '10px';

    const uploadBtn = document.createElement('button');
    uploadBtn.className = 'action-btn';
    uploadBtn.textContent = 'Upload CSV file';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'action-btn';
    cancelBtn.textContent = 'Cancel Upload';

    btnContainer.appendChild(uploadBtn);
    btnContainer.appendChild(cancelBtn);
    output.appendChild(btnContainer);
    scrollToBottom();

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.csv';
    fileInput.style.display = 'none';

    uploadBtn.onclick = () => {
        fileInput.click();
    };

    cancelBtn.onclick = () => {
        printLine("Upload cancelled.", true);
        output.removeChild(btnContainer);
        document.body.removeChild(fileInput);
    };

    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];

        if (output.contains(btnContainer)) {
            output.removeChild(btnContainer);
        }

        if (!file) {
            printLine("Upload cancelled.", true);
            return;
        }

        printLine(`File selected: ${file.name}`);
        printLine("Connecting to local AirSense Backend (http://localhost:5000/api/analyze)...");

        const formData = new FormData();
        formData.append('file', file);
        formData.append('api_key', geminiKey);

        const inputLine = document.querySelector('.input-line');
        inputLine.style.display = 'none';

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'item';
        output.appendChild(loadingDiv);

        let frameIdx = 0;
        const spinnerFrames = [
            '⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'
        ];

        const loadingInterval = setInterval(() => {
            loadingDiv.innerHTML = `<span class="gradient-text">${spinnerFrames[frameIdx]}</span> Uploading & Analyzing CSV Data... This may take up to 60 seconds.`;
            frameIdx = (frameIdx + 1) % spinnerFrames.length;
        }, 80);

        scrollToBottom();

        try {
            const response = await fetch('http://localhost:5000/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                printLine(`<span style="color:#ff5555">Error: ${data.error || 'Server error'}</span>`, true);
                if (data.details) printLine(data.details);


                const errorStr = (data.error || '').toLowerCase();
                const detailStr = (data.details || '').toLowerCase();
                const isAuthError = response.status === 401 || response.status === 403 || response.status === 429 ||
                    errorStr.includes('api key') || errorStr.includes('exhausted') ||
                    detailStr.includes('api key') || detailStr.includes('exhausted');

                if (isAuthError) {
                    printLine("<span style='color:#ff5555'>The saved API key appears to be invalid or exhausted. Please re-enter a valid key.</span>", true);
                    localStorage.removeItem('gemini_api_key');
                    geminiKey = '';
                    setTimeout(startAirSenseWizard, 1500);
                }
                return;
            }


            renderAnalysisResults(data.analysis, data.articles, data.charts, data.thought);


        } catch (error) {
            printLine("<span style='color:#ff5555'>Error: Could not connect to the AirSense Backend. Make sure the Flask server is running on port 5000.</span>", true);
        } finally {
            clearInterval(loadingInterval);
            if (output.contains(loadingDiv)) {
                output.removeChild(loadingDiv);
            }
            inputLine.style.display = 'flex';

            if (document.body.contains(fileInput)) {
                document.body.removeChild(fileInput);
            }
            commandInput.focus();
        }
    });

    document.body.appendChild(fileInput);
}

function renderAnalysisResults(analysis, articles, charts, thought) {
    if (thought) {
        printLine("");
        printLine("<span style='color: #888888'>[ AGENT REASONING TRACE ]</span>", true);
        printLine(`<span style='color: #666666; font-style: italic;'>${thought}</span>`, true);
        printLine("");
    }

    printLine("<span style='color: #4aea5dff'>[ ANALYSIS RESULTS ]</span>", true);
    printLine(analysis);

    if (charts && (charts.line_chart || charts.bar_chart || charts.histogram)) {
        printLine("");
        printLine("<span style='color: #4aea5dff'>[ GENERATED VISUALIZATIONS ]</span>", true);
        printLine("Loading base64 encoded plotting data from Matplotlib...");

        const chartTypes = [
            { key: 'line_chart', name: 'AQI Trend Line Chart' },
            { key: 'bar_chart', name: 'Pollutants Bar Chart' },
            { key: 'histogram', name: 'AQI Distribution Histogram' }
        ];

        chartTypes.forEach(chart => {
            if (charts[chart.key]) {
                const div = document.createElement('div');
                div.className = 'item';
                div.innerHTML = `<div style="color: #62b7ec; margin-top: 10px; margin-bottom: 5px;">> ${chart.name}</div>`;

                const img = document.createElement('img');
                img.src = `data:image/png;base64,${charts[chart.key]}`;
                img.style.maxWidth = "100%";
                img.style.border = "1px solid var(--text-color)";

                div.appendChild(img);
                output.appendChild(div);
            }
        });

        scrollToBottom();
    }

    if (articles && articles.length > 0) {
        printLine("");
        printLine("<span style='color: #4aea5dff'>[ RELATED NEWS ]</span>", true);
        articles.forEach((article, idx) => {
            printLine(`${idx + 1}. ${article.title}`);
            printLine(`   Source: ${article.source.name} | Published: ${article.publishedAt.split('T')[0]}`);
            printLine(`   <a href="${article.url}" target="_blank" class="news-link">Read Article</a>`, true);
            printLine("");
        });
    }

    printLine("");
    printLine("");
    printLine("\n\n<span style='color: #4aea5dff'>Analysis Routine Complete.</span>", true);

    const navContainer = document.createElement('div');
    navContainer.className = 'item';
    navContainer.style.marginTop = '20px';

    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'action-btn';
    downloadBtn.textContent = 'Download Analysis Report';
    downloadBtn.onclick = () => generatePDF(analysis, thought, charts);

    const exitBtn = document.createElement('button');
    exitBtn.className = 'action-btn';
    exitBtn.textContent = 'Exit to main program';
    exitBtn.onclick = () => {
        output.innerHTML = '';
        printLine("Returning to main terminal...", true);
        setTimeout(() => {
            output.innerHTML = '';
            updateInput();
        }, 1000);
    };

    navContainer.appendChild(downloadBtn);
    navContainer.appendChild(exitBtn);
    output.appendChild(navContainer);
    scrollToBottom();
}

async function generatePDF(analysis, thought, charts) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.setFont("helvetica", "bold");
    doc.setFontSize(16);
    doc.setTextColor(0, 0, 0);
    doc.text("AIRSENSE AI ANALYSIS REPORT", 10, 20);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    let currentX = 10;
    const part1 = "Created and Analyzed by AirSense AI - Developed by ";
    doc.text(part1, currentX, 30);
    currentX += doc.getTextWidth(part1);

    doc.setTextColor(0, 0, 255);
    const part2 = "Stephen Sii";
    doc.textWithLink(part2, currentX, 30, { url: "https://stephensii.netlify.app/" });
    currentX += doc.getTextWidth(part2);

    doc.setTextColor(0, 0, 0);
    const part3 = " from ";
    doc.text(part3, currentX, 30);
    currentX += doc.getTextWidth(part3);

    doc.setTextColor(0, 0, 255);
    const part4 = "Latton Lab";
    doc.textWithLink(part4, currentX, 30, { url: "https://lattonlab.netlify.app/" });

    let yPos = 45;

    if (thought) {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.setTextColor(100, 100, 100);
        doc.text("[ Agent Thinking Logs ]", 10, yPos);
        yPos += 8;
        doc.setFont("courier", "italic");
        doc.setFontSize(10);
        const splitThought = doc.splitTextToSize(thought, 180);
        splitThought.forEach(line => {
            if (yPos > 280) { doc.addPage(); yPos = 20; }
            doc.text(line, 10, yPos);
            yPos += 5;
        });
    }

    doc.addPage();
    yPos = 20;

    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0);
    doc.text("[ Analysis Report ]", 10, yPos);
    yPos += 8;
    doc.setFont("courier", "normal");
    doc.setFontSize(10);
    const splitAnalysis = doc.splitTextToSize(analysis, 180);

    for (let i = 0; i < splitAnalysis.length; i++) {
        if (yPos > 280) {
            doc.addPage();
            yPos = 20;
        }
        doc.text(splitAnalysis[i], 10, yPos);
        yPos += 5;
    }

    if (charts) {
        doc.addPage();
        yPos = 20;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.text("[ Visualizations ]", 10, yPos);
        yPos += 10;

        const chartKeys = ['line_chart', 'bar_chart', 'histogram'];
        for (const key of chartKeys) {
            if (charts[key]) {
                if (yPos > 200) { doc.addPage(); yPos = 20; }
                doc.addImage(`data:image/png;base64,${charts[key]}`, 'PNG', 10, yPos, 180, 80);
                yPos += 90;
            }
        }
    }

    doc.save("AirSense_Analysis_Report.pdf");
}

window.onload = async () => {
    commandInput.disabled = true;
    printBanner();
    await typeText(introText, 2);
    commandInput.disabled = false;
    commandInput.focus();
    updateInput();
};
