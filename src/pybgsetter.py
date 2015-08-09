#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import pygtk
#pygtk.require('2.0')
import gtk
import gtk.glade

import os, subprocess, re, gettext

__version__ = "0.5"
__author__  = "Pável Varela Rodríguez <neonskull@gmail.com>"

BIN_DIR = os.path.abspath(os.path.dirname(__file__))
if os.path.exists("%s/pybgsetterui.glade" % BIN_DIR):
    SHARE_DIR = BIN_DIR
elif os.path.exists("/usr/share/pybgsetter/pybgsetterui.glade"):
    SHARE_DIR = "/usr/share/pybgsetter"
else:
    print("Check your installation!!!")
    print("I can't find pybgsetterui.glade in: '%s' nor '%s'!" 
                                                          % (BIN_DIR,
                                                             "/usr/share/pybgsetter"
                                                             ))
    os.sys.exit(1)
UI_FILE = "%s/pybgsetterui.glade" % SHARE_DIR


################################################################################
# i18n Initialization
################################################################################
PARENT_DIR = os.path.join(SHARE_DIR, os.path.pardir)
i18n_base_dir = os.path.join(PARENT_DIR, "po", "i18n")
i18n_lang = os.environ["LANG"].split("_")[0]
if os.path.exists(os.path.join(i18n_base_dir, i18n_lang)):
    translation = gettext.translation('pybgsetter', i18n_base_dir)
    translation.install(unicode=1)
    gtk.glade.textdomain('pybgsetter')
    gtk.glade.bindtextdomain('pybgsetter', i18n_base_dir)
else:
    gettext.install('pybgsetter', unicode=1)
    gtk.glade.textdomain('pybgsetter')



SUPPORTED_BACKENDS = ["hsetroot", "Esetroot", "habak", "feh"]
SUPPORTED_OPTIONS = ["ScaledAndCentered", "Scaled", "Centered", "Tiled"]
SUPPORTED_IMAGE_TYPES = ["*.png", "*.jpeg", "*.jpg", "*.jpe", "*.bmp", "*.gif", 
                         "*.PNG", "*.JPEG", "*.JPG", "*.JPE", "*.BMP", "*.GIF"]



def discoverInstalledApps():
    apps = []
    for app in SUPPORTED_BACKENDS:
        app_binary = subprocess.Popen(
                                      ["which", app],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                     ).communicate()[0]
        if app_binary:
            apps.append(app)
    return apps


def calculateAspectRatio(resolution, returnAsString = False):
    (width, height) = [float(item) for item in resolution.split("x")]
    aspectRatio = round((width / height), 2)
    
    if returnAsString:
        AR_MAP = {        
                  "1.78" : "16:9",
                  "1.6"  : "16:10",
                  "1.33" : "4:3",
                  "1.25" : "5:4"
                 }
        if AR_MAP.has_key(str(aspectRatio)):
            aspectRatio = str(AR_MAP[str(aspectRatio)])
    return aspectRatio


class NotImageException(Exception):
    def __init__(self, imageFileName):
        self.msg = _("Not a valid image file: %s") % imageFileName
        super(NotImageException, self).__init__(self.msg)


class Screen(object):
    def __init__(self):
        xrandrOutput = subprocess.Popen(
                                      ["xrandr"],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                     ).communicate()[0]
        
        res = re.compile(".*\ ([0-9]{3,4}x[0-9]{3,4})\+[0-9]+\+[0-9]+\ .*")
        for line in xrandrOutput.splitlines():
            m = res.match(line)
            if m:
                self.__resolution = m.groups()[0]
                break
        
        (self.__width, self.__height) = self.__resolution.split("x")
        self.__width = int(self.__width)
        self.__height = int(self.__height)
        self.__aspectRatio = calculateAspectRatio(self.__resolution)
        self.__aspectRatioAsString = calculateAspectRatio(self.__resolution, True)


    def getWidth(self):
        return self.__width


    def getHeight(self):
        return self.__height


    def getResolution(self):
        return self.__resolution


    def getAspectRatio(self, returnAsString = False):
        if returnAsString:
            return self.__aspectRatioAsString
        return self.__aspectRatio


class ImageHandler(object):
    def __init__(self, screen):
        self.screen = screen
        self.imageFileName = ""
        self.imageInfo = {}
        self.modifiedImageFile = os.path.join(os.path.expanduser("~/"), ".bgimage.png")


    def setImageFileName(self, imageFileName):
        self.imageFileName = imageFileName
        self.fillImageInformation()


    def fillImageInformation(self):
        OUTPUT = subprocess.Popen(
                                  ["identify", self.imageFileName],
                                  stdout=subprocess.PIPE
                                 ).communicate()[0].splitlines()[0]
        OUTPUT = OUTPUT.replace(self.imageFileName, "").strip().split(" ")
        self.imageInfo["Format"]      = OUTPUT[0]
        self.imageInfo["Resolution"]  = OUTPUT[1]
        self.imageInfo["Size"]        = OUTPUT[5]
        self.imageInfo["AspectRatio"] = calculateAspectRatio(self.imageInfo["Resolution"])
        self.imageInfo["AspectRatioAsString"] = calculateAspectRatio(self.imageInfo["Resolution"], True)


    def prepareScaledImage(self):
        screenAspectRatio = self.screen.getAspectRatio()
        (width, height) = self.imageInfo["Resolution"].split("x")
        
        if (self.imageInfo["AspectRatio"] < screenAspectRatio):
            height = self.screen.getHeight()
            width = int(round(height * self.imageInfo["AspectRatio"], 1))
        else:
            width = self.screen.getWidth()
            height = int(round(width / self.imageInfo["AspectRatio"], 1))

        destResolution = "%sx%s" % (width, height)
        subprocess.call(["convert", "-resize", destResolution, self.imageFileName, self.modifiedImageFile])
        self.imageFileName = self.modifiedImageFile



class BaseBgHandler(object):
    def __init__(self, screen=None, option=None):
        self.screen = screen
        if self.screen == None:
            self.screen = Screen()
        self.option = "optionScaledAndCentered"
        if option:
            self.option = option
        self.restoreBgCommand = ""
        self.rcFile = os.path.join(os.path.expanduser("~/"), ".bgrc")
        self.bgImage = ImageHandler(self.screen)
        
        self.appCommand = ""
        self.appParams = {
                          "optionScaledAndCentered": "",
                          "optionScaled": "",
                          "optionCentered": "",
                          "optionTiled": ""
                         }

    def applyBg(self):
        subprocess.call(self.createCommand())
        self.writeBgRcFile()


    def setBgImage(self, imageFileName):
        self.bgImage.setImageFileName(imageFileName)


    def setOption(self, option):
        self.option = option


    def writeBgRcFile(self):
        self.restoreBgCommand = self.createCommand(True)
        fileHandler = file(self.rcFile, "w")
        fileHandler.write(self.restoreBgCommand)
        fileHandler.close()


    def createCommand(self, asString = False):
        command = [self.appCommand, self.appParams[self.option], self.bgImage.imageFileName]
        if asString:
            return "%s %s \"%s\"\n" % (command[0], command[1], command[2])
        return command


    def __str__(self):
        return self.__class__.__name__


class HsetrootBgHandler(BaseBgHandler):
    def __init__(self, screen, option=None):
        super(HsetrootBgHandler, self).__init__(screen, option)
        self.appCommand = "hsetroot"
        self.appParams = {
                          "optionScaledAndCentered": "-full",
                          "optionScaled": "-fill",
                          "optionCentered": "-center",
                          "optionTiled": "-tile"
                         }


class EsetrootBgHandler(BaseBgHandler):
    def __init__(self, screen, option=None):
        super(EsetrootBgHandler, self).__init__(screen, option)
        self.appCommand = "Esetroot"
        self.appParams = {
                          "optionScaledAndCentered": "-fit",
                          "optionScaled": "-scale",
                          "optionCentered": "-center",
                          "optionTiled": ""
                         }


class HabakBgHandler(BaseBgHandler):
    def __init__(self, screen, option=None):
        super(HabakBgHandler, self).__init__(screen, option)
        self.appCommand = "habak"
        self.appParams = {
                          "optionScaledAndCentered": "-mS",
                          "optionScaled": "-ms",
                          "optionCentered": "-mC",
                          "optionTiled": ""
                         }


class FehBgHandler(BaseBgHandler):
    def __init__(self, screen, option=None):
        super(FehBgHandler, self).__init__(screen, option)
        self.appCommand = "feh"
        self.appParams = {
                          "optionScaledAndCentered": "--bg-center",
                          "optionScaled": "--bg-scale",
                          "optionCentered": "--bg-center",
                          "optionTiled": "--bg-tile"
                         }
        self.fehBgFile = os.path.expanduser("~/.fehbg")


    def applyBg(self):
        if self.option == "optionScaledAndCentered":
            self.__prepareScaledImage()
        super(FehBgHandler, self).applyBg()


    def writeBgRcFile(self):
        super(FehBgHandler, self).writeBgRcFile()
        fileHandler = file(self.fehBgFile, "w")
        fileHandler.write(self.restoreBgCommand)
        fileHandler.close()


    def __prepareScaledImage(self):
        if self.bgImage.imageInfo["AspectRatio"] != self.screen.getAspectRatio():
            self.bgImage.prepareScaledImage()
        else:
            self.option = "optionScaled"


class HelpDialog(gtk.Dialog):
    def __init__(self):
        super(HelpDialog, self).__init__(_("pyBgSetter Quick Help"))
        self.set_icon_name("preferences-desktop-wallpaper")
        self.set_size_request(550, 400)
        text = gtk.Label()
        text.set_line_wrap(True)
        text.set_selectable(True)
        text.set_size_request(500, -1)
        text.set_alignment(0.3, 0.0)
        text.set_markup(open(os.path.join(SHARE_DIR, "extras", "HELP")).read())
        sb = gtk.ScrolledWindow()
        sb.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sb.add_with_viewport(text)
        self.vbox.pack_start(sb)
        btnClose = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.action_area.pack_start(btnClose)
        btnClose.connect("clicked", lambda w: self.destroy())
        self.show_all()
        self.run()
        self.destroy()


class AboutDialog(gtk.AboutDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.set_icon_name("preferences-desktop-wallpaper")
        self.set_name("pyBgSetter")
        self.set_version(__version__)
        self.set_title(_("About pyBgSetter"))
        self.set_copyright("Copyright (C) 2010, Pável Varela Rodríguez")
        self.set_comments(_("Multi-backend GUI for desktop wallpaper setting\n(Feh, Habak, Esetroot, Hsetroot)"))
        self.set_logo_icon_name("preferences-desktop-wallpaper")
        self.set_license(open(os.path.join(SHARE_DIR, "extras", "LICENSE")).read())
        self.set_website("http://archlinux.me/neonskull")
        self.set_authors(["Pável Varela Rodríguez <neonskull@gmail.com>"])
        translators = [
                       "Spanish: Pável Varela Rodríguez <neonskull@gmail.com>",
                       "French: Jan Dlabal <dlabaljan@gmail.com>",
                       "Czech: Jan Dlabal <dlabaljan@gmail.com>",
                       "Polish: Jan Dlabal <dlabaljan@gmail.com>",
                       "German: Stefan Husmann <Stefan-Husmann@t-online.de>",
                      ]
        self.set_translator_credits("\n".join(translators))
        self.run()
        self.destroy()


class SelectImageDialog(gtk.FileChooserDialog):
    def __init__(self, currentFolder):
        super(SelectImageDialog, self).__init__(
                                                _("Select image file"),
                                                buttons=(
                                                         gtk.STOCK_CANCEL,
                                                         gtk.RESPONSE_REJECT,
                                                         gtk.STOCK_OK,
                                                         gtk.RESPONSE_ACCEPT
                                                        )
                                               )
        filters = gtk.FileFilter()
        filters.set_name(_("Image Files"))
        for pattern in SUPPORTED_IMAGE_TYPES:
            filters.add_pattern(pattern)

        self.add_filter(filters)
        self.set_current_folder(currentFolder)



class PyBgSetter(object):
    def __init__(self, screen):
        self.screen = screen
        self.bgHandler = None


    def setBgHandler(self, backendName):
        if backendName == "feh":
            self.bgHandler = FehBgHandler(self.screen)
        elif backendName == "habak":
            self.bgHandler = HabakBgHandler(self.screen)
        elif backendName == "Esetroot":
            self.bgHandler = EsetrootBgHandler(self.screen)
        elif backendName == "hsetroot":
            self.bgHandler = HsetrootBgHandler(self.screen)
            

    def setBgOption(self, option):
        self.bgHandler.setOption(option)


    def setBgImage(self, imageFileName):
        if not self.isImageFile(imageFileName):
            raise NotImageException(imageFileName)
        self.bgHandler.setBgImage(imageFileName)


    def applyBg(self):
        self.bgHandler.applyBg()


    def getBgImageFileName(self):
        return self.bgHandler.bgImage.imageFileName


    def getBgImageInfo(self):
        return self.bgHandler.bgImage.imageInfo


    def isImageFile(self, imageFileName):
        output = subprocess.Popen(
                                  ["identify", imageFileName],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                 ).communicate()[0]
        return (output not in ["", None, False])


class PyBgSetterCLI(object):
    def __init__(self, backend, imageFileName, option="optionScaledAndCentered"):
        self.screen = Screen()
        self.bgSetter = PyBgSetter(self.screen)
        self.bgSetter.setBgHandler(backend)
        self.bgSetter.setBgImage(imageFileName)
        self.bgSetter.setBgOption(option)
        self.bgSetter.applyBg()
        


class PyBgSetterUI(object):
    def __init__(self, ui_file, bgHandlerApps):
        self.ui_file = ui_file
        self.__initUI()
        self.screen = Screen()
        self.bgSetter = PyBgSetter(self.screen)
        
        self.screenInformation.set_markup("<i><b>%s:</b></i> %s [%s]"
                                           % (
                                              _("Screen"),
                                              self.screen.getResolution(),
                                              self.screen.getAspectRatio(True)
                                             )
                                          )
        
        if bgHandlerApps[0] == "hsetroot":
            self.backendHsetroot.clicked()
        elif bgHandlerApps[0] == "Esetroot":
            self.backendEsetroot.clicked()
        elif bgHandlerApps[0] == "habak":
            self.backendHabak.clicked()
        elif bgHandlerApps[0] == "feh":
            self.backendFeh.clicked()
        
        if "hsetroot" not in bgHandlerApps:
            self.backendHsetroot.set_sensitive(False)
        if "Esetroot" not in bgHandlerApps:
            self.backendEsetroot.set_sensitive(False)
        if "habak" not in bgHandlerApps:
            self.backendHabak.set_sensitive(False)
        if "feh" not in bgHandlerApps:
            self.backendFeh.set_sensitive(False)


    def setBgLayoutOption(self, clickedWidget):
        self.bgSetter.setBgOption(clickedWidget.get_name())
        if self.fileOpenEntry.get_text():
            self.applyButton.set_sensitive(True)
            self.applyAndCloseButton.set_sensitive(True)


    def applyBg(self, widget):
        self.bgSetter.setBgImage(self.fileOpenEntry.get_text())
        self.refreshSelectedOption()
        self.bgSetter.applyBg()
        self.applyButton.set_sensitive(False)
        self.applyAndCloseButton.set_sensitive(False)


    def selectImage(self, widget):
        if self.fileOpenEntry.get_text():
            currentFolder= os.path.dirname(self.fileOpenEntry.get_text())
        else:
            currentFolder = os.path.expanduser("~/")
        
        selectImageDialog = SelectImageDialog(currentFolder)
        
        if selectImageDialog.run() == gtk.RESPONSE_ACCEPT:
            try:
                imageFileName = selectImageDialog.get_filename()
                self.bgSetter.setBgImage(imageFileName)
                self.fileOpenEntry.set_text(imageFileName)
                self.updatePreview()
                self.updateImageInformation()
                self.applyButton.set_sensitive(True)
                self.applyAndCloseButton.set_sensitive(True)
            except NotImageException as e:
                selectImageDialog.destroy()
                errorMsg = gtk.MessageDialog(
                                     type=gtk.MESSAGE_ERROR,
                                     buttons=gtk.BUTTONS_OK,
                                     message_format=e.msg)
                errorMsg.run()
                errorMsg.destroy()
        
        selectImageDialog.destroy()


    def updatePreview(self):
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.bgSetter.getBgImageFileName(), 300, 225)
        self.imagePreview.set_from_pixbuf(pixbuf)


    def updateImageInformation(self):
        template =  "<i><b>%s:</b></i> %s [%s]\n"
        template += "<i><b>%s:</b></i> %s\n"
        template += "<i><b>%s:</b></i> %s"
        
        imageInfo = self.bgSetter.getBgImageInfo()
        information = template % (
                                  _("Resolution"),
                                  imageInfo["Resolution"],
                                  imageInfo["AspectRatioAsString"],
                                  _("Format"),
                                  imageInfo["Format"],
                                  _("Size"),
                                  imageInfo["Size"]
                                 )
        self.imageInformation.set_markup(information)


    def backendToHsetroot(self, widget=None):
        self.bgSetter.setBgHandler("hsetroot")
        self.optionTiled.set_sensitive(True)
        self.refreshSelectedOption()


    def backendToEsetroot(self, widget=None):
        self.bgSetter.setBgHandler("Esetroot")
        if self.optionTiled.get_active():
            self.optionScaledAndCentered.clicked()
        self.optionTiled.set_sensitive(False)
        self.refreshSelectedOption()


    def backendToHabak(self, widget=None):
        self.bgSetter.setBgHandler("habak")
        if self.optionTiled.get_active():
            self.optionScaledAndCentered.clicked()
        self.optionTiled.set_sensitive(False)
        self.refreshSelectedOption()


    def backendToFeh(self, widget=None):
        self.bgSetter.setBgHandler("feh")
        self.optionTiled.set_sensitive(True)
        self.refreshSelectedOption()


    def applyAndClose(self, widget):
        self.applyBg(widget)
        self.closeApp()


    def refreshSelectedOption(self):
        if self.optionScaledAndCentered.get_active():
            self.optionScaledAndCentered.clicked()
        elif self.optionTiled.get_active():
            self.optionTiled.clicked()
        elif self.optionCentered.get_active():
            self.optionCentered.clicked()
        else:
            self.optionScaled.clicked()


    def showHelpDialog(self, widget):
        HelpDialog()


    def showAboutDialog(self, widget):
        AboutDialog()


    def closeApp(self, *args):
        gtk.main_quit()


    def __initUI(self):
        self.Widgets = gtk.glade.XML(self.ui_file, domain='pybgsetter')
        self.Widgets.signal_autoconnect(self)
        
        for widget in self.Widgets.get_widget_prefix(""):
            widgetName = widget.get_name()
            if not hasattr(self, widgetName):
                setattr(self, widgetName, widget)
        
        self.applyAndCloseButton.set_sensitive(False)
        self.applyButton.set_sensitive(False)
        self.MainWindow.show_all()



if __name__ == "__main__":
    apps = discoverInstalledApps()
    if len(apps) == 0:
        appsString = ""
        for app in SUPPORTED_BACKENDS:
            appsString += "\n- %s" % app.capitalize()
        msg = _("You must install at least one of the following apps: %s") % appsString
        errorMsg = gtk.MessageDialog(
                                     type=gtk.MESSAGE_ERROR,
                                     buttons=gtk.BUTTONS_OK,
                                     message_format=msg)
        errorMsg.run()
        errorMsg.destroy()
        os.sys.exit(1)
    else:
        if len(os.sys.argv) == 1:
            PyBgSetterUI(UI_FILE, apps)
            gtk.main()
        
        else:
            # Removing script from argv
            app = os.path.basename(os.sys.argv[0])
            os.sys.argv = os.sys.argv[1:]
            
            def usage():
                print(_("pyBgSetter: Multi-backend Desktop Background Setter (v%s)") % __version__)
                print(_("Usage:"))
                print("  %s [--backend=<BACKEND>] [--option=<OPTION>] image_file\n" % app)
                print(_("  Supported Backends: %s") % ", ".join(SUPPORTED_BACKENDS))
                print(_("  Supported Options:  %s") % ", ".join(SUPPORTED_OPTIONS))
                print(_("\nExample:"))
                print("  %s --backend=hsetroot --option=Tiled ~/wallpaper.png\n" % app)
            
            if "-h" in os.sys.argv or "--help" in os.sys.argv:
                usage()
                os.sys.exit(0)
            
            # Getting Backend
            _backend = [item for item in os.sys.argv if item.startswith("--backend=")]
            if len(_backend) == 1:
                backend = _backend[0].split("=")[1]
                if not backend or backend not in SUPPORTED_BACKENDS or backend not in apps:
                    print(_("Unknown or Not Installed Backend: '%s'") % backend)
                    usage()
                    os.sys.exit(1)
                os.sys.argv.remove(_backend[0])
            else:
                backend = apps[0]
            
            # Getting Option
            _option = [item for item in os.sys.argv if item.startswith("--option=")]
            if len(_option) == 1:
                option = _option[0].split("=")[1]
                if not option or option not in SUPPORTED_OPTIONS:
                    print(_("Unknown Option: '%s'") % option)
                    usage()
                    os.sys.exit(1)
                os.sys.argv.remove(_option[0])
            else:
                option = "ScaledAndCentered"
            
            # Getting Image to use as background
            imageFileName = os.path.abspath(os.sys.argv[0])
            
            if not os.path.exists(imageFileName):
                print(_("File does not exists: '%s'") % imageFileName)
                os.sys.exit(1)
            
            EXT = os.path.splitext(imageFileName)
            if len(EXT) == 2:
                EXT = EXT[1]
            else:
                EXT = ""
            if EXT not in [ext.split("*")[1] for ext in SUPPORTED_IMAGE_TYPES]:
                print(_("File type not supported: '%s'") % EXT)
                os.sys.exit(1)


            try:
                print(_("Settings:"))
                print(_("  Backend: %s") % backend)
                print(_("  Option: %s") % option)
                print(_("  Image: %s") % imageFileName)
                PyBgSetterCLI(backend, imageFileName, "option%s" % option)
            except NotImageException as e:
                print(_("ERROR: %s") % e.msg)
                os.sys.exit(1)


