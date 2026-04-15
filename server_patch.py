# --- IMPROVED COMMAND EXECUTION ---

async def execute_command(user_text: str) -> str:
    original = user_text
    text = user_text.lower().strip()
    log.info(f"Parsing: {text}")

    # Normalize wake words
    text = re.sub(r"^(hey\s+)?jarvis[, ]*", "", text)

    if not text:
        return "Yes sir?"

    # -------- OPEN FILE EXPLORER --------
    if any(phrase in text for phrase in [
        "open files", "open file explorer", "show files", "launch explorer"
    ]):
        open_file_explorer()
        return "Opening File Explorer, sir."

    # -------- QUICK FOLDERS --------
    quick_paths = {
        "downloads": "~/Downloads",
        "desktop": "~/Desktop",
        "documents": "~/Documents"
    }

    for key, path in quick_paths.items():
        if key in text and "open" in text:
            open_file_explorer(path)
            return f"Opening {key.capitalize()}, sir."

    # -------- OPEN ANY FOLDER (SMART SEARCH) --------
    if "open" in text and "folder" in text:
        folder = text.split("folder")[-1].strip()

        full = expand_path(folder)
        if os.path.exists(full):
            open_file_explorer(full)
            return f"Opening folder '{folder}', sir."

        result = search_files(folder)
        if "Found:" in result:
            first_match = result.split("\n")[1]
            open_file_explorer(os.path.dirname(first_match))
            return f"Found and opening related folder for '{folder}', sir."

        return f"Folder '{folder}' not found, sir."

    # -------- CREATE FOLDER --------
    if "create folder" in text or "make folder" in text:
        folder = text.split("folder")[-1].strip()
        return create_folder(folder)

    # -------- DELETE FOLDER --------
    if "delete folder" in text or "remove folder" in text:
        folder = text.split("folder")[-1].strip()
        return delete_folder(folder)

    # -------- FILE COMMANDS --------
    if "create file" in text:
        filename = text.split("file")[-1].strip()
        return create_file(filename)

    if "read file" in text:
        filename = text.split("file")[-1].strip()
        return read_file(filename)

    if "delete file" in text:
        filename = text.split("file")[-1].strip()
        return delete_file(filename)

    # -------- TIME / DATE --------
    if "time" in text:
        return f"The time is {datetime.now().strftime('%I:%M %p')}, sir."

    if "date" in text:
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}, sir."

    # -------- FALLBACK AI --------
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are JARVIS. Be brief."},
                {"role": "user", "content": original}
            ],
            max_tokens=100
        )
        return completion.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "System error, sir."
