#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2015 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import webbrowser

from electrumsv.i18n import _
import electrumsv.web as web
from electrumsv.address import Address
from electrumsv.exceptions import FileImportFailed
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QFileDialog, QMenu, QTreeWidgetItem)
from .util import MyTreeWidget


class ContactList(MyTreeWidget):
    filter_columns = [0, 1]  # Key, Value

    def __init__(self, parent):
        MyTreeWidget.__init__(self, parent, self.create_menu, [_('Name'), _('Address')], 0, [0])
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)

    def on_permit_edit(self, item, column):
        # openalias items shouldn't be editable
        return item.text(1) != "openalias"

    def on_edited(self, item, column, _prior):
        self.parent.set_contact(item.text(0), item.text(1))

    def import_contacts(self):
        wallet_folder = self.parent.get_wallet_folder()
        filename, __ = QFileDialog.getOpenFileName(self.parent, "Select your wallet file",
                                                   wallet_folder)
        if not filename:
            return
        try:
            self.parent.contacts.import_file(filename)
        except FileImportFailed as e:
            self.parent.show_message(str(e))
        self.on_update()

    def create_menu(self, position):
        menu = QMenu()
        selected = self.selectedItems()
        if not selected:
            menu.addAction(_("New contact"), self.parent.new_contact_dialog)
            menu.addAction(_("Import file"), self.import_contacts)
        else:
            keys = [item.text(1) for item in selected]
            column = self.currentColumn()
            column_title = self.headerItem().text(column)
            column_data = '\n'.join([item.text(column) for item in selected])
            menu.addAction(_("Copy {}").format(column_title),
                           lambda: self.parent.app.clipboard().setText(column_data))
            if column in self.editable_columns:
                item = self.currentItem()
                menu.addAction(_("Edit {}").format(column_title),
                               lambda: self.editItem(item, column))
            menu.addAction(_("Pay to"), lambda: self.parent.payto_contacts(keys))
            menu.addAction(_("Delete"), lambda: self.parent.delete_contacts(keys))
            URLs = [web.BE_URL(self.config, 'addr', Address.from_string(key))
                    for key in keys if Address.is_valid(key)]
            if URLs:
                menu.addAction(_("View on block explorer"),
                               lambda: [webbrowser.open(URL) for URL in URLs])

        menu.exec_(self.viewport().mapToGlobal(position))

    def on_update(self):
        item = self.currentItem()
        current_key = item.data(0, Qt.UserRole) if item else None
        self.clear()
        for key in sorted(self.parent.contacts.keys()):
            _type, name = self.parent.contacts[key]
            item = QTreeWidgetItem([name, key])
            item.setData(0, Qt.UserRole, key)
            self.addTopLevelItem(item)
            if key == current_key:
                self.setCurrentItem(item)
