import base64
import os
import subprocess
import sys
from datetime import datetime

from just_heic import convert_file as convert_heic
from lxml import etree
from playwright.sync_api import sync_playwright

### functions: filesystem


def create_directory(directory_path):
    # Check if the directory exists
    if not os.path.exists(directory_path):
        # If the directory doesn't exist, create it
        os.makedirs(directory_path)

    # Return the directory path that existed or was created (should match the input)
    return directory_path


def script_path():
    # Get the path of the current script
    script_path = os.path.abspath(__file__)

    # Return the directory of the current script
    return os.path.dirname(script_path) + "\\"


def list_xml_files(directory):
    # Get all files in the directory
    files = os.listdir(directory)

    # Filter out the XML files and remove the file extension
    xml_files = [os.path.splitext(file)[0] for file in files if file.endswith(".xml")]

    return xml_files


### functions: xml


def parse_huge_xml(xml_path):
    # Create a custom parser with the Huge option enabled
    parser = etree.XMLParser(huge_tree=True)

    # Parse XML file using the custom parser
    return etree.parse(xml_path, parser)


def rename_null_mms_data(parsed_xml):
    null_counter: int = 0
    for part in parsed_xml.iter("part"):
        content_type = part.get("ct")

        match content_type:
            case "video/mp4":
                extension = "mp4"
            case "video/3gpp":
                extension = "3gp"
            case "image/heic":
                extension = "heic"
            case _:
                extension = None

        if extension:
            file_name = part.get("cl")
            if file_name == "null":
                null_counter += 1
                file_name = f"""unnamed_{null_counter:03d}.{extension}"""
                part.set("cl", file_name)

    return parsed_xml


def remove_mms_text(parsed_xml):
    # Collect elements to remove to avoid modifying tree while iterating
    mms_to_remove = []

    # First, collect all SMS text messages for comparison
    sms_texts = set()
    for sms in parsed_xml.iter("sms"):
        body = sms.get("body")
        if body and body.strip():
            # Normalize text: strip whitespace and normalize line endings
            normalized_text = " ".join(body.strip().split())
            sms_texts.add(normalized_text)

    for mms in parsed_xml.iter("mms"):
        parts = mms.find("parts")
        if parts is not None:  # Check if all parts are either SMIL or text content (no media content)
            is_text_only = True
            mms_text_content = ""

            for part in parts.findall("part"):
                ct = part.get("ct")
                text = part.get("text")

                # Check if this part contains text content (but ignore SMIL layout)
                if text and text.strip() and ct != "application/smil":
                    # This part has actual message text content, so collect it
                    mms_text_content += text.strip() + " "

                # Check for media content types
                if ct and ct not in ("application/smil", "text/plain", ""):
                    is_text_only = False
                    break  # If all parts are text-only (SMIL + text), check if there's a matching SMS
            if is_text_only and mms_text_content.strip():
                # Normalize MMS text the same way as SMS text
                normalized_mms_text = " ".join(mms_text_content.strip().split())

                # Only remove if there's a matching SMS with the same text content
                if normalized_mms_text in sms_texts:
                    mms_to_remove.append(mms)  # Remove collected elements
    for mms in mms_to_remove:
        parent = mms.getparent()
        if parent is not None:
            parent.remove(mms)

    return parsed_xml


def transform(parsed_xml, xslt_path: str, html_path: str):
    # Parse XSLT file
    xslt = etree.parse(xslt_path)

    # Create a transform function
    transform = etree.XSLT(xslt)

    # Apply the transformation to the XML file
    result = transform(parsed_xml)

    # Write the result to an HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(result))

    return result


def get_mms_data_from_xml(parsed_xml, content_type: str):
    for part in parsed_xml.iter("part"):
        if part.get("ct") == content_type:
            # Return the "cl" (filename) and "data" attributes as a tuple
            yield (part.get("cl"), part.get("data"))


### functions: heic


def convert_heic_to_jpg(filename_heic: str, base64_heic: str, output_directory: str):
    filepath_heic = output_directory + filename_heic
    filepath_jpg = output_directory + filename_heic + ".jpg"

    # Decode the base64 .heic file
    with open(filepath_heic, "wb") as f:
        f.write(base64.b64decode(base64_heic))

    convert_heic(filepath_heic, filepath_jpg)


### functions: videos


def convert_3gp_to_mp4(filename_3gp: str, base64_3gp: str, output_directory: str):
    filepath_3gp = output_directory + filename_3gp
    filepath_mp4 = output_directory + filename_3gp + ".mp4"
    filepath_image = output_directory + filename_3gp + ".jpg"

    # Decode the base64 .3gp file
    with open(filepath_3gp, "wb") as f:
        f.write(base64.b64decode(base64_3gp))

    # Convert the .3gp file to .mp4 using ffmpeg
    subprocess.run(
        [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            "-nostats",
            "-loglevel",
            "0",
            "-y",
            "-i",
            filepath_3gp,
            filepath_mp4,
        ]
    )

    # Save a jpg of the first frame using ffmpeg
    subprocess.run(
        [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            "-nostats",
            "-loglevel",
            "0",
            "-y",
            "-i",
            filepath_3gp,
            "-vframes",
            "1",
            "-ss",
            "00:00:00",
            "-update",
            "1",
            filepath_image,
        ]
    )

    # Remove the .3gp file
    if os.path.isfile(filepath_3gp) and os.path.isfile(filepath_mp4) and os.path.isfile(filepath_image):
        os.remove(filepath_3gp)


def extract_mp4(filename_mp4: str, base64_mp4: str, output_directory: str):
    filepath_mp4 = output_directory + filename_mp4
    filepath_image = output_directory + filename_mp4 + ".jpg"

    # Decode the base64 .mp4 file
    with open(filepath_mp4, "wb") as f:
        f.write(base64.b64decode(base64_mp4))

    # Save a jpg of the first frame using ffmpeg
    subprocess.run(
        [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            "-nostats",
            "-loglevel",
            "0",
            "-y",
            "-i",
            filepath_mp4,
            "-vframes",
            "1",
            "-ss",
            "00:00:00",
            "-update",
            "1",
            filepath_image,
        ]
    )


### functions: pdf


def html_to_pdf(html_path, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{html_path.replace('\\', '/')}", wait_until="networkidle", timeout=60000)
        page.pdf(
            path=output_path,
            format="Letter",
            margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
            print_background=True,
            display_header_footer=True,
            header_template="""<div></div>""",
            footer_template="""<div style="font-size: 10px; text-align: right; width: 100%; margin-right: 1cm;">pg <span class="pageNumber"></span>/<span class="totalPages"></span></div>""",
        )
        browser.close()


### functions: do the things


def do_the_things(directory_input: str):
    xml_files = list_xml_files(directory_input)

    print()

    for file in xml_files:
        directory_output = create_directory(directory_input + "\\Text Messages\\" + file + "\\")

        print(directory_input + "\\" + file + ".xml")

        print("", datetime.now().strftime("%H:%M:%S"), "Parsing file")
        xml = parse_huge_xml(directory_input + "\\" + file + ".xml")
        xml = remove_mms_text(xml)
        xml = rename_null_mms_data(xml)

        print("", datetime.now().strftime("%H:%M:%S"), "Converting images: heic")
        for content in get_mms_data_from_xml(xml, "image/heic"):
            convert_heic_to_jpg(*content, directory_output)

        print("", datetime.now().strftime("%H:%M:%S"), "Converting videos: 3gp")
        for content in get_mms_data_from_xml(xml, "video/3gpp"):
            convert_3gp_to_mp4(*content, directory_output)

        print("", datetime.now().strftime("%H:%M:%S"), "Extracting videos: mp4")
        for content in get_mms_data_from_xml(xml, "video/mp4"):
            extract_mp4(*content, directory_output)

        print("", datetime.now().strftime("%H:%M:%S"), "Converting xml to html")
        transform(
            xml,
            script_path() + "__assets__/asbar.xslt",
            directory_output + file + ".html",
        )

        print("", datetime.now().strftime("%H:%M:%S"), "Converting html to pdf")
        html_to_pdf(directory_output + file + ".html", directory_output + file + ".pdf")

        print("", datetime.now().strftime("%H:%M:%S"), "All done")
        print(directory_output, "\n")


def start():
    if len(sys.argv) == 1:
        do_the_things(os.getcwd())
    elif len(sys.argv) != 2:
        print("Usage: asbar [directory_path]")
    else:
        do_the_things(sys.argv[1])


### __main__
if __name__ == "__main__":
    start()
