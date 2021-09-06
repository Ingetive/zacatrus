// pos_logo_change js
//console.log("custom callleddddddddddddddddddddd")
odoo.define('pos_logo_change.pos',function(require){
	"use strict";
	var models = require('point_of_sale.models');
	var chrome=require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var QWeb = core.qweb;

    var _t = core._t;



    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var company_model = _.find(this.models, function(model){ return model.model === 'res.company'; });
            company_model.fields.push('logo','street','city','state_id');
            // Push Other fields of res.company so we can access those fields in POS... 
            return _super_posmodel.initialize.call(this, session, attributes);
        },
        
    });
    
	chrome.OrderSelectorWidget.include({
		init: function(parent, options) {
		    this._super(parent, options);
		    this.pos.get('orders').bind('add remove change',this.renderElement,this);
		    this.pos.bind('change:selectedOrder',this.renderElement,this);
		    
		    //this custom code is for pos_logo
		    var $image = self.$('#pos-logo');
		        $image.attr("src",'/web/image?model=pos.config&field=pos_logo&id='+this.pos.config.id);
		        $image.css( { marginLeft : "15px", marginTop : "5px", 'border-radius':'3px' } ); //width:'100px',
		},
	});

	var OrderSuper = models.Order;
	var posorder_super = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			this.barcode = this.barcode || "";
			this.set_barcode();
			posorder_super.initialize.call(this,attr,options);
		},

		set_barcode: function(){
			var self = this;	
			var temp = Math.floor(100000000000+ Math.random() * 9000000000000)
			self.barcode =  temp.toString();
		},

		export_as_JSON: function() {
			var self = this;
			var loaded = OrderSuper.prototype.export_as_JSON.call(this);
			loaded.barcode = self.barcode;
			return loaded;
		},

	});



	screens.ReceiptScreenWidget.include({
		show: function () {
			this._super(); 
			var order = this.pos.get_order();
			$("#barcode_print").barcode(
				order.barcode, // Value barcode (dependent on the type of barcode)
				"code128" // type (string)
			);
		},
	});


});;
