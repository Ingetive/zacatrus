#!/bin/bash

rsync -av $(dirname "$0")/../zacatrus_base/* /usr/lib/python3/dist-packages/odoo/addons/zacatrus_base/
#rsync -av $(dirname "$0")/../zacatrus/* /usr/lib/python3/dist-packages/odoo/addons/zacatrus/
rsync -av $(dirname "$0")/../zacasocios/* /usr/lib/python3/dist-packages/odoo/addons/zacasocios/
rsync -av $(dirname "$0")/../pos_tarjezaca/* /usr/lib/python3/dist-packages/odoo/addons/pos_tarjezaca/
sudo killall -9 odoo && sudo service odoo restart