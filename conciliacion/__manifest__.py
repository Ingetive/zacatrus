# -*- coding: utf-8 -*-
# © 2021 Voodoo - <hola@voodoo.es>
{
    'name': "Conciliación",
    'description': "Conciliación",
    'category': 'Uncategorized',
    'sequence': 1,
    'version': '14.0.0',
    'application': True,
    'depends': [
        'account',
        'account_bank_statement_import'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_bank_statement.xml',
        'wizard/account_bank_statement_import.xml'
    ],
}
