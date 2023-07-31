# what is this

I bought a FreeX wifi connected label printer for printing labels, mostly for labelling bins. I needed a quick command line script for printing the contents of a bin. Since I have a lot of bins, going through some fancy UI program, setting the printer parameters, etc, just to print 1 of several hundred labels is too annoying. I forked OmniIoT/pdf2tspl mostly to see if I could easily communicate with the FreeX label printer via a relatively simple python program. 

Since the FreeX printer openly supports TSPL2 this was an easy place to start.

So what is this? Based on the original README.md:

1. a tool that takes a PDF and prints it on a label, and
2. a print server that speaks the AppSocket protocol, so you can print to it from CUPS anyway. (I will likely remove this since the FreeX drivers work with CUPS out of the box.)

# how do I print a thing

You need to have `pdftoppm` on your `PATH` - it's installed by the `poppler` package (at least on my Gentoo system).

Identify the device node for your printer. For my USB printer, it's `/dev/usb/lp0`.

Find the PDF you want to print. Note that at the moment, only the first page is printed. The PDF will be scaled so that the whole thing fits on the label.

Then you can:

```
./pdf2tspl.py file_to_print.pdf /dev/usb/lp0
```

...and hopefully receive a label.

# how do I print a thing with CUPS

If `pdf2tspl.py` is working for you, you can run `appsocket_print_server.py /dev/path/to/your/printer`.

Then, in CUPS:

1. go to Add Printer
2. choose AppSocket/HP JetDirect
3. set the Connection to `socket://hostname`, where `hostname` is the machine running the print server; use `localhost` if you're just running it on the same machine
4. set the name as you wish
5. when prompted for a Make, select Generic
6. when prompted for a Model, select Generic PDF Printer
7. hit Add Printer
8. set the default page size to A6 (for reasonable scaling on 100x150mm labels) and colour mode to Black and White
