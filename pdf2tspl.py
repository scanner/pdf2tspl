#!/usr/bin/env python3

import tempfile
import subprocess
import dataclasses
import socket


@dataclasses.dataclass
class Image:
    width: int
    height: int
    data: bytes


def convert_pdf(pdfname, args=[]):
    with tempfile.NamedTemporaryFile(suffix=".pbm") as pbmfile:
        subprocess.check_call(
            ["pdftoppm", "-mono", "-singlefile"]
            + args
            + [pdfname, pbmfile.name.removesuffix(".pbm")]
        )

        header = pbmfile.readline()
        if header.strip() != b"P4":
            raise ValueError("unrecognised image format")
        width_height = pbmfile.readline().decode("ascii")
        data = bytes(x ^ 0xFF for x in pbmfile.read())

    width, height = map(int, width_height.strip().split())
    return Image(width, height, data)


def convert_pdf_scaled(pdfname, max_width, max_height):
    im = convert_pdf(pdfname)
    aspect = im.width / im.height
    max_aspect = max_width / max_height

    if aspect < max_aspect:
        max_width = int(max_height * aspect) - 1
    else:
        # pdftoppm tends to make it 1px too wide
        max_width -= 1
        max_height = int(max_width / aspect)

    args = ["-scale-to-x", str(max_width), "-scale-to-y", str(max_height)]
    im = convert_pdf(pdfname, args)

    assert im.width <= max_width + 1
    assert im.height <= max_height

    return im


def pdf2tspl(filename, labelwidth_mm=100, labelheight_mm=150, dpi=203.2):
    labelwidth = int(round(labelwidth_mm / 25.4 * dpi))
    labelheight = int(round(labelheight_mm / 25.4 * dpi))

    image = convert_pdf_scaled(filename, labelwidth, labelheight)

    paste_x = (labelwidth - image.width) // 2
    paste_y = (labelheight - image.height) // 2
    row_bytes = (image.width + 7) // 8

    COMMANDS = [
        f"SIZE {labelwidth_mm}mm,{labelheight}mm",  # width, length
        "GAP 0.120,0.000",
        "SPEED 5",
        "DENSITY 8",
        "DIRECTION 0,0",
        "REFERENCE 0,0",
        "OFFSET 0.000",
        "SHIFT 0",
        "SET PEEL OFF",
        "SET CUTTER OFF",
        "SET PARTIAL_CUTTER OFF",
        "SET TEAR ON",
        "CLS",
        f"BITMAP {paste_x},{paste_y},{row_bytes},{image.height},0,{str(image.data,'iso-8859-1')}",
        "PRINT 1,1",
    ]
    cmd = "\r\n".join(COMMANDS) + "\r\n"
    tspl = bytes(cmd, "iso-8859-1")

    # tspl = b"\r\n\r\nSIZE %d mm,%d mm\r\nCLS\r\nBITMAP %d,%d,%d,%d,0," % (
    #     labelwidth_mm,
    #     labelheight_mm,
    #     paste_x,
    #     paste_y,
    #     row_bytes,
    #     image.height,
    # )
    # tspl += image.data
    # tspl += b"\r\nPRINT 1,1\r\n"
    return tspl


if __name__ == "__main__":
    # from PyPDF2 import PdfFileWriter, PdfFileReader
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Convert a PDF to TSPL to send to a label printer."
    )
    parser.add_argument("pdf_file", help="The PDF to convert.")
    parser.add_argument(
        "--tspl_printer",
        help="The network device to write the TSPL to. Expects <hostname>:<port> or <ipaddress>:<port>",
        default="lwip.apricot.com:9100"
    )

    parser.add_argument(
        "-x",
        "--width",
        type=int,
        default=102,
        help="The width of the label, in millimetres.",
    )
    parser.add_argument(
        "-y",
        "--height",
        type=int,
        default=76,
        help="The height of the label, in millimetres.",
    )
    parser.add_argument(
        "-d",
        "--dpi",
        type=float,
        default=203.2,
        help="Resolution of the printer. Defaults to 8 dots per mm (203.2 dpi)",
    )
    args = parser.parse_args()

    tspl_host, tspl_port = args.tspl_printer.split(":")

    # inputpdf = PdfFileReader(open(args.pdf_file, "rb"))

    # for i in range(inputpdf.numPages):
    #     output = PdfFileWriter()
    #     output.addPage(inputpdf.getPage(i))
    #     temp_pdf_name = "temp/document-page%s.pdf" % i
    #     with open(temp_pdf_name, "wb") as outputStream:
    #         output.write(outputStream)

    tspl = pdf2tspl(
        args.pdf_file,
        labelwidth_mm=args.width,
        labelheight_mm=args.height,
        dpi=args.dpi,
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((tspl_host, int(tspl_port)))
        s.sendall(tspl)
        # if args.tspl_file == "-":
        #     sys.stdout.buffer.write(tspl)
        # else:
        #     with open(args.tspl_file, "wb") as fp:
        #         fp.write(tspl)
