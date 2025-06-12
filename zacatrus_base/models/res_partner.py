from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import requests
import json
from datetime import datetime, timedelta
import base64
import hmac
import hashlib
import time
import re

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    pos = fields.Char(
        string='POS última compra',
        help='Point of Sale identifier',
        index=True,
        tracking=True
    )

    @api.model
    def _init_pos_field(self):
        """Initialize the pos field if it doesn't exist"""
        try:
            self.env.cr.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='res_partner' 
                AND column_name='pos'
            """)
            if not self.env.cr.fetchone():
                self.env.cr.execute("""
                    ALTER TABLE res_partner 
                    ADD COLUMN pos varchar
                """)
                self.env.cr.commit()
        except Exception as e:
            _logger.error("Error initializing pos field: %s", str(e))
    