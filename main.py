import base64
import os
import subprocess
import sys
from datetime import datetime

import pdfkit
from lxml import etree

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


def get_3gp_base64_from_xml(parsed_xml):
    # Find the "part" element with ct="video/3gpp"
    nulls: int = 0
    for part in parsed_xml.iter("part"):
        if part.get("ct") == "video/3gpp":
            filename = part.get("cl")
            if filename == "null":
                nulls += 1
                filename = f"""unnamed_3gp_{nulls:03d}.3gp"""
            # Return the "cl" (filename) and "data" attributes as a tuple
            yield (filename, part.get("data"))


def get_mp4_base64_from_xml(parsed_xml):
    # Find the "part" element with ct="video/mp4"
    nulls: int = 0
    for part in parsed_xml.iter("part"):
        if part.get("ct") == "video/mp4":
            filename = part.get("cl")
            if filename == "null":
                nulls += 1
                filename = f"""unnamed_mp4_{nulls:03d}.mp4"""
            # Return the "cl" (filename) and "data" attributes as a tuple
            yield (filename, part.get("data"))


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
            "true",
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
            "true",
            filepath_image,
        ]
    )


### functions: pdf


def html_to_pdf(html_path: str, pdf_path: str):
    # Define options for pdfkit configuration
    options = {
        "enable-local-file-access": "",
        "footer-right": "[page]",
        "footer-font-size": "10",
    }

    # Create a pdfkit configuration with the path to wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

    # Convert the HTML file to PDF
    pdfkit.from_file(html_path, pdf_path, options=options, configuration=config)


### functions: do the things


def do_the_things(directory_input: str):
    xml_files = list_xml_files(directory_input)

    print()

    for file in xml_files:
        directory_output = create_directory(directory_input + "\\Text Messages\\" + file + "\\")

        print(directory_input + "\\" + file + ".xml")

        print("", datetime.now().strftime("%H:%M:%S"), "Parsing file")
        xml = parse_huge_xml(directory_input + "\\" + file + ".xml")

        print("", datetime.now().strftime("%H:%M:%S"), "Converting videos: 3gp")
        for video in get_3gp_base64_from_xml(xml):
            convert_3gp_to_mp4(*video, directory_output)

        print("", datetime.now().strftime("%H:%M:%S"), "Extracting videos: mp4")
        for video in get_mp4_base64_from_xml(xml):
            extract_mp4(*video, directory_output)

        print("", datetime.now().strftime("%H:%M:%S"), "Converting xml to html")
        transform(
            xml,
            script_path() + "asbar.xslt",
            directory_output + file + ".html",
        )

        print("", datetime.now().strftime("%H:%M:%S"), "Converting html to pdf")
        html_to_pdf(directory_output + file + ".html", directory_output + file + ".pdf")

        print("", datetime.now().strftime("%H:%M:%S"), "All done")
        print(directory_output, "\n")


def start():
    if len(sys.argv) != 2:
        print("Usage: python script.py directory_path")
    else:
        do_the_things(sys.argv[1])


### __main__
if __name__ == "__main__":
    start()
