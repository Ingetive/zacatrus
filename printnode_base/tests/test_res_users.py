# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_users')  # can be run by test-tag
class TestPrintNodeUsers(TestPrintNodeCommon):
    """
    Tests of User model methods
    """

    def test_get_shipping_label_printer(self):
        """
        Test for the correct assignment of shipping label printer for user
        """

        with self.assertRaises(UserError):
            self.user.get_shipping_label_printer()

        self.user.user_label_printer = self.printer
        test_printer = self.user.get_shipping_label_printer()
        self.assertEqual(self.printer.id, test_printer.id, "Wrong get shipping label printer")

        self.user.user_label_printer = None

        with self.assertRaises(UserError):
            self.user.get_shipping_label_printer()

        self.env.company.company_label_printer = self.printer
        test_printer = self.user.with_env(self.env).get_shipping_label_printer()
        self.assertEqual(self.printer.id, test_printer.id, "Wrong get shipping label printer")

    def test_get_scales(self):
        """
        Test for the correct assignment of scales for user
        """

        self.user.printnode_scales = self.scales
        test_scales = self.user.get_scales()
        self.assertEqual(test_scales.id, self.scales.id, "Wrong assignment of scales for user")

        self.user.printnode_scales = None
        test_scales = self.user.get_scales()
        self.assertNotEqual(test_scales.id, self.scales.id)

        self.env.company.printnode_scales = self.scales
        test_scales = self.user.with_env(self.env).get_scales()
        self.assertEqual(test_scales.id, self.scales.id, "Wrong assignment of scales for user")

    def test_get_printer_within_report_download(self):
        """
        Test for the correct get printer within report download
        """

        company_printer = self.company_printer
        user_printer = self.user_printer

        self.company.write({'printnode_printer': company_printer.id})
        self.user.write({'printnode_printer': user_printer.id})

        # Expected UserRule Printer
        self.action_button.write({'printer_id': False})
        printer, printer_bin = self.user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.user_rule.printer_id.id)

        # Expected User's Printer
        self.user_rule.write({'report_id': self.delivery_slip_report.id})
        printer, printer_bin = self.user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.user.printnode_printer.id)

        # Expected Company's Printer
        self.user.write({'printnode_printer': False})
        printer, printer_bin = self.user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.company.printnode_printer.id)

    def test_get_workstation_device(self):
        """
        Test for helper method to setting device for current workstation
        """

        self.assertIsNone(self.user._get_workstation_device('something'))

        self.assertIsNone(self.user.with_context({
            'printnode_workstation_printer_id': 'lalala'
        })._get_workstation_device('printnode_workstation_printer_id'))

        # Workstation_printer
        self.assertEqual(self.user.with_context({
            'printnode_workstation_printer_id': self.printer.id
        })._get_workstation_device('printnode_workstation_printer_id'), self.printer)

        # Workstation_scales
        self.assertEqual(self.user.with_context({
            'printnode_workstation_scales_id': self.scales.id
        })._get_workstation_device('printnode_workstation_scales_id'), self.scales)

    def test_validate_device_id(self):
        """
        Test for correct validate device id
        """

        devices = {
            'printnode_workstation_printer_id': self.printer.id,
            'printnode_workstation_label_printer_id': self.printer.id,
            'printnode_workstation_scales_id': self.scales.id,
        }

        device_names = self.user.validate_device_id(devices)

        self.assertEqual(device_names['printnode_workstation_printer_id'], self.printer.name)
        self.assertEqual(device_names['printnode_workstation_label_printer_id'], self.printer.name)
        self.assertEqual(device_names['printnode_workstation_scales_id'], self.scales.name)
