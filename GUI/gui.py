import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class CreateScreen():
    def __init__(self, path, parent):
        self.parent = parent
        self.vbox = Gtk.VBox(spacing=6)

        user = Gtk.Box(spacing=6)

        user.pack_start(Gtk.Label("Username:"), True, True, 0)
        self.user_input = Gtk.Entry()
        user.pack_start(self.user_input, True, True, 0)
        self.vbox.pack_start(user, True, True, 0)

        name = Gtk.Box(spacing=6)
        user.pack_start(Gtk.Label("Keyname:"), True, True, 0)
        self.keyname_input = Gtk.Entry()
        name.pack_start(self.keyname_input, True, True, 0)
        self.vbox.pack_start(name, True, True, 0)

        passwd = Gtk.Box(spacing=6)
        passwd.pack_start(Gtk.Label("Password:"), True, True, 0)
        self.pass_input = Gtk.Entry()
        passwd.pack_start(self.pass_input, True, True, 0)
        self.vbox.pack_start(passwd, True, True, 0)

        button = Gtk.Button.new_with_label("Create")
        self.vbox.pack_start(button, True, True, 0)
        self.parent.add(self.vbox)

class KeyWizard(Gtk.Window):

    def __init__(self, path):
        Gtk.Window.__init__(self, title="LiverpoolFS")
        self.set_border_width(10)

        self.vbox = Gtk.VBox(spacing=6)
        self.add(self.vbox)

        label = Gtk.Label("USB Drive Inserted!\nDo you want to create a new key, or use an existing one?")
        self.vbox.pack_start(label, True, True, 0)

        hbox = Gtk.Box(spacing=6)
        self.vbox.pack_start(hbox, True, True, 0)

        button = Gtk.Button.new_with_label("Create Key")
        button.connect("clicked", self.create)
        hbox.pack_start(button, True, True, 0)

        button = Gtk.Button.new_with_label("Use Existing Key")
        button.connect("clicked", self.use)
        hbox.pack_start(button, True, True, 0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        self.create = Gtk.VBox(spacing=6)
        user = Gtk.Box(spacing=6)

        user.pack_start(Gtk.Label("Username:"), True, True, 0)
        self.user_input = Gtk.Entry()
        user.pack_start(self.user_input, True, True, 0)
        self.create.pack_start(user, True, True, 0)

        name = Gtk.Box(spacing=6)
        user.pack_start(Gtk.Label("Keyname:"), True, True, 0)
        self.keyname_input = Gtk.Entry()
        name.pack_start(self.keyname_input, True, True, 0)
        self.create.pack_start(name, True, True, 0)

        passwd = Gtk.Box(spacing=6)
        passwd.pack_start(Gtk.Label("Password:"), True, True, 0)
        self.pass_input = Gtk.Entry()
        passwd.pack_start(self.pass_input, True, True, 0)
        self.create.pack_start(passwd, True, True, 0)

        button = Gtk.Button.new_with_label("Create")
        self.create.pack_start(button, True, True, 0)



    def create(self, button):
        self.remove(self.vbox)
        self.add(self.create)

    def use(self, button):
        print("\"Open\" button was clicked")

    def on_close_clicked(self, button):
        Gtk.main_quit()

win = KeyWizard("test")
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
