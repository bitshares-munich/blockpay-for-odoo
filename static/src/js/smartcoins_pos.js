odoo.define('smartcoins_pos.smartcoins_pos', function (require) {
"use strict";

var Class   = require('web.Class');
var Model   = require('web.Model');
var session = require('web.session');
var core    = require('web.core');
var screens = require('point_of_sale.screens');
var gui     = require('point_of_sale.gui');
var pos_model = require('point_of_sale.models');
var utils = require('web.utils');

var _t      = core._t;
var QWeb = core.qweb;

var BarcodeParser = require('barcodes.BarcodeParser');
var PopupWidget = require('point_of_sale.popups');
var ScreenWidget = screens.ScreenWidget;
var PaymentScreenWidget = screens.PaymentScreenWidget;
var ReceiptScreenWidget = screens.ReceiptScreenWidget;
var round_pr = utils.round_precision;

var merchant_account = "";
var bt_coin_id = 0;
var generated_input_address = "";
var sm_coins_obj = {};
var bt_sm_coins_obj = {};
var bt_selected_coin_name= "";

ReceiptScreenWidget.include({
	
	render_receipt: function() {
        var order = this.pos.get_order();
        var alternate_payment_method = localStorage.getItem("alternate_payment_method") !== null ? 
				JSON.parse(localStorage.getItem("alternate_payment_method")) : null;
		console.log('----In receipt alter method', alternate_payment_method);
        var paymentLines = order.get_paymentlines();
        paymentLines.forEach(function(line_obj) {
            var payment_method = line_obj.name.split(' ');
            if(payment_method.length > 1){
            	if(payment_method[1] == "[" + alternate_payment_method["symbol"] + "]"){
            		var curr_uia_title = line_obj.name.split("]");
            		line_obj.name = curr_uia_title[0] + " " +  alternate_payment_method["amount"] + "]"
            		localStorage.removeItem("alternate_payment_method");
            	}
            }
        });
        this.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                widget:this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: paymentLines,
            }));
    }
	
});

PaymentScreenWidget.include({
    
    render_paymentmethods: function() {
	var self = this;
	var methods = $(QWeb.render('PaymentScreen-Paymentmethods', { widget:this }));
	    methods.on('click','.paymentmethod',function(){
                self.click_paymentmethods($(this).data('id'));
            });
	    methods.on('click','.smartcoins_start',function(){
	    	var inst = $('[data-remodal-id=modal]').remodal();
		 	inst.open();
	    	var smartcoins = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_bt_coins');

       smartcoins.then(function(result){
           var smartcoins = result.smartcoins;
		   console.log("smartcoinsArray",smartcoins);
		   var contents = $('.container-smartcoins');
		   console.log("div",contents);
	       contents.html('');
	       contents.append('<div class="button paymentmethods smt_btn" style="background-image:url(../../smartcoins_pos/static/img/bts.png)">Smartcoins</div>');
	       for(var i = 0, len = Math.min(smartcoins.length,1000); i < len; i++){
				var smartcoin = smartcoins[i];
				var img = "";
				if (smartcoin.name.toLowerCase() == "dogecoin"){
					  img = "doge.png";
				}else if (smartcoin.name.toLowerCase() == "litecoin"){
					  img = "ltc.png";
				}else if (smartcoin.name.toLowerCase() == "bitshares"){
					  img = "bts.png";
				}else if (smartcoin.name.toLowerCase() == "dash"){
					  img = "dash.png";
				}else if (smartcoin.name.toLowerCase() == "nubits" || smartcoin.name.toLowerCase() == "nushares"){
					  img = "nbt.png";
				}else if (smartcoin.name.toLowerCase() == "peercoin"){
					  img = "ppc.png";
				}else {
				  img = "bitcoin-logo.png";
				}
	           var child = '<div class="button paymentmethods smt_btn" style="background-image:url(../../smartcoins_pos/static/img/'+img+')" data-id="'+smartcoin.id+'">'+smartcoin.name+'</div>';
	           contents.append(child);
       		   }
       		   $('.container-smartcoins').delegate('.smt_btn','click',function(event){
	                var selected = $(this).html();
	                if (selected.toLowerCase() == "smartcoins"){
	                	self.gui.show_screen('smartcoinsqr');
						var interValId = setInterval(function(){ 
							self.check_sm_transaction_status(interValId);
					   }, 5000)
	                }else{
	                	var order = self.pos.get_order();
				    	var order_transaction = {"id" : "", "input_address" : "", "transaction_status" : "", "amount" : -1};
				    	order_transaction["id"] = order.name.split(' ')[1];
				    	localStorage.setItem("order_transaction", JSON.stringify(order_transaction));

				    	var paymentScreenTimer = setInterval(function(){ 
				    		self.check_bt_transaction_status(paymentScreenTimer)
						   }, 5000);
				    	bt_coin_id = $(this).data('id');
				    	console.log("newID",$(this).data('id'));
			    	    bt_selected_coin_name = selected;
			            self.gui.show_screen('bt_smartcoinsqr');
	                }
	                inst.close();
	            });
       },function(err){
           console.log(err);
       });
	    });
	    methods.on('click','.bt_bridge_choices',function(){
	    	var order = self.pos.get_order();
	    	var order_transaction = {"id" : "", "input_address" : "", "transaction_status" : "", "amount" : -1};
	    	order_transaction["id"] = order.name.split(' ')[1];
	    	localStorage.setItem("order_transaction", JSON.stringify(order_transaction));
	    	
	    	self.gui.show_screen('smartcoinslist');
	    	var paymentScreenTimer = setInterval(function(){ 
	    		self.check_bt_transaction_status(paymentScreenTimer)
			   }, 5000);
	    });
	return methods;
    },
    
    stopPaymentScreenTimer: function(intervalId){
    	console.log('----stop payment screen timer');
		clearInterval(intervalId);
    },
    
    check_sm_transaction_status : function(interValId){
    	var self = this;
    	console.log('--------Start payment screen timer');
		var sm_order_transaction = localStorage.getItem("sm_coin_order_transaction") !== null ? 
				JSON.parse(localStorage.getItem("sm_coin_order_transaction")) : null;
		var sm_order_transaction_status = localStorage.getItem("sm_coin_transaction_status");
		if(sm_order_transaction_status !== null && sm_order_transaction_status == "true"){
			self.stopPaymentScreenTimer(interValId);
			console.log('----printing sm order object');
			var order_id = sm_order_transaction.callback.split("/")[5];
			var order_payment = new Model('smartcoins_pos.transactions_block_info').call('get_paid_amount', {order_id:order_id});

	        order_payment.then(function(result){
	        	console.log('-----Order Payment');
	        	console.log('----Transactions',result);
	        	var sum = 0;
	        	var order = self.pos.get_order();
			    
	        	if("order_payment_amount" in result){
	        		console.log('----if cond');
	        		sum = result["order_payment_amount"];
	        		var customRegister = JSON.parse(JSON.stringify(self.pos.cashregisters[0]));
				    customRegister.journal_id[1] = sm_coins_obj.smartcoins.title.split(" ")[0];
				    order.add_paymentline(customRegister);
				    order.selected_paymentline.paid = true;
				    order.selected_paymentline.amount = sum;
				    self.order_changes();
				    self.reset_input();
				    self.render_paymentlines();
				    order.trigger('change', order); // needed so that export_to_JSON gets triggered
	        	}
	        	else if("transactions" in result){
	        		console.log('----else cond');
	        		var transactions = result["transactions"];
	        		for (i = 0; i < transactions.length; i++) { 
	        			var cRegister1 = JSON.parse(JSON.stringify(self.pos.cashregisters[0]));
	        			if(transactions[i].isRewardPointAsset){
	        				
	        				var title1 = sm_coins_obj.smartcoins.title.split(" ")[0] + " " + transactions[i].symbol;
	        				console.log('----transaction rp asset', title1);
	        				cRegister1.journal_id[1] = sm_coins_obj.smartcoins.title.split(" ")[0] + " [" + transactions[i].symbol + "]";
	        				var alternate_payment_method = {"symbol" : transactions[i].symbol, "amount" : transactions[i].rp_amount};
	        				localStorage.setItem("alternate_payment_method", JSON.stringify(alternate_payment_method));
	        			}
	        			else{
	        				var title2 = sm_coins_obj.smartcoins.title.split(" ")[0];
	        				console.log('----sm asset', title2);
	        				cRegister1.journal_id[1] = sm_coins_obj.smartcoins.title.split(" ")[0];
	        			}
					    order.add_paymentline(cRegister1);
					    order.selected_paymentline.paid = true;
					    order.selected_paymentline.amount = transactions[i].amount;
	        		}
	        		
				    self.order_changes();
				    self.reset_input();
				    self.render_paymentlines();
				    order.trigger('change', order); // needed so that export_to_JSON gets triggered
	        	}
	            
			    
			    
	        },function(err){
	            console.log(err);
	        });
			
			localStorage.removeItem("sm_coin_order_transaction");
			localStorage.removeItem("sm_coin_transaction_status");
		}
    },
    
    check_bt_transaction_status : function(paymentScreenTimer){
    	var self = this;
    	console.log('--------Start payment screen timer');
	   var order_transaction = JSON.parse(localStorage.getItem("order_transaction"));
	   if(order_transaction["transaction_status"]){
		   self.stopPaymentScreenTimer(paymentScreenTimer);
		   console.log("Adding Payment");
		   var order = self.pos.get_order();
		   
		   $.ajax({
			   url: "https://blocktrades.us/api/v2/simple-api/transactions?inputAddress=" +  generated_input_address,
			   type: "get",
			   success : function(result){
				   if(result.length && result[0].inputNumberOfConfirmations > 0){
					   self.bt_object = result
					   console.log('-----Alt coins transaction confirmed', self.bt_object);
//				   Apply condition if output coin type == BTS
//				   else only show output amount
					   if(self.bt_object[0].outputCoinType == "bts"){
						   var smartcoins = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_data');
						   
					       smartcoins.then(function(result){
					            console.log('----Sm result if ',result);
					            self.smcoin = result;
					            var exchange_rate = new Model('smartcoins_pos.smartcoins_pos').call('getCurrency', {base_asset_id:"1.3.0", quote_asset_id: result["smartcoins"]["asset_id"] });
					            exchange_rate.then(function(result){
					                console.log('----Rate BTS/Smart coin',result);
					                var customRegister = JSON.parse(JSON.stringify(self.pos.cashregisters[0]));
					                customRegister.journal_id[1] = self.smcoin.smartcoins.name + " [" + bt_selected_coin_name + "]";
					                var converted_amount = (result * +self.bt_object[0].outputAmount ).toFixed(2);
					                var alternate_payment_method = {"symbol" : bt_selected_coin_name, "amount" : +self.bt_object[0].outputAmount};
			        				localStorage.setItem("alternate_payment_method", JSON.stringify(alternate_payment_method));
					                order.add_paymentline(customRegister);
					                order.selected_paymentline.paid = true;
					                order.selected_paymentline.amount = converted_amount //self.bt_object[0].outputAmount;
					                self.order_changes();
					                self.reset_input();
					                self.render_paymentlines();
					                order.trigger('change', order); // needed so that export_to_JSON gets triggered
					                self.store_transaction(order.name.split(' ')[1], generated_input_address, true);
					                localStorage.removeItem("order_transaction")
					            },function(err){
					                console.log(err);
					            });
					        },function(err){
					            console.log(err);
					        });
					   }
					   else{
						   var smartcoins = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_data');
						   
					       smartcoins.then(function(result){
					            console.log('----Sm result else ',result);
					            self.smcoin = result;
					            var customRegister = JSON.parse(JSON.stringify(self.pos.cashregisters[0]));
				     		   customRegister.journal_id[1] = self.smcoin.smartcoins.name + " [" + bt_selected_coin_name + "]";
				                order.add_paymentline(customRegister);
				                order.selected_paymentline.paid = true;
				                order.selected_paymentline.amount = self.bt_object[0].outputAmount //self.bt_object[0].outputAmount;
				                var alternate_payment_method = {"symbol" : bt_selected_coin_name, "amount" : +self.bt_object[0].outputAmount};
		        				localStorage.setItem("alternate_payment_method", JSON.stringify(alternate_payment_method));
				                self.order_changes();
				                self.reset_input();
				                self.render_paymentlines();
				                order.trigger('change', order); // needed so that export_to_JSON gets triggered
				                self.store_transaction(order.name.split(' ')[1], generated_input_address, true);
				                localStorage.removeItem("order_transaction")
					            
					        },function(err){
					            console.log(err);
					        });
						   
					   } //if(result[0].outputCoinType == "bts") ended
				   
					   
				   }//if(result.length && result[0].inputNumberOfConfirmations > 0) ended
			   }
			 });
		   
	   }
    },
    
    store_transaction: function(order_id, dep_address, trx){
    	var store_transaction = new Model('smartcoins_pos.bt_smartcoins_transactions').
		   call('store_transactions', {order : order_id, deposit_address : dep_address, transaction_status : trx});
		   
		   store_transaction.then(function(result){
			   console.log('------transaction stored successfully');
			   generated_input_address = "";
	        },function(err){
	            console.log(err);
	        });
    }
});

/*--------------------------------------*\
 |          THE DOM CACHE               |
\*======================================*/

// The Dom Cache is used by various screens to improve
// their performances when displaying many time the 
// same piece of DOM.
//
// It is a simple map from string 'keys' to DOM Nodes.
//
// The cache empties itself based on usage frequency 
// stats, so you may not always get back what
// you put in.

var DomCache = core.Class.extend({
    init: function(options){
        options = options || {};
        this.max_size = options.max_size || 2000;

        this.cache = {};
        this.access_time = {};
        this.size = 0;
    },
    cache_node: function(key,node){
        var cached = this.cache[key];
        this.cache[key] = node;
        this.access_time[key] = new Date().getTime();
        if(!cached){
            this.size++;
            while(this.size >= this.max_size){
                var oldest_key = null;
                var oldest_time = new Date().getTime();
                for(key in this.cache){
                    var time = this.access_time[key];
                    if(time <= oldest_time){
                        oldest_time = time;
                        oldest_key  = key;
                    }
                }
                if(oldest_key){
                    delete this.cache[oldest_key];
                    delete this.access_time[oldest_key];
                }
                this.size--;
            }
        }
        return node;
    },
    clear_node: function(key) {
        var cached = this.cache[key];
        if (cached) {
            delete this.cache[key];
            delete this.access_time[key];
            this.size --;
        }
    },
    get_node: function(key){
        var cached = this.cache[key];
        if(cached){
            this.access_time[key] = new Date().getTime();
        }
        return cached;
    },
});

/*--------------------------------------*\
 |         THE SMARTCOINS LIST              |
\*======================================*/

// The smartcoinsqr displays the QR code of smartcoins,
// and allows the cashier to make payment.

var SmartCoinsQRScreenWidget = ScreenWidget.extend({
    template: 'SmartCoinsQRScreenWidget',

    init: function(parent, options){
        this._super(parent, options);
        this.smartcoin_cache = new DomCache();
        var self = this;
        var smartcoins = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_data');
        var reward_uia = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_uia_data');
        var uia_settings = new Model('smartcoins_pos.smartcoins_pos').call('get_uia_settings');
        
        uia_settings.then(function(result){
            console.log('-----UIA settings');
        	console.log(result);
        	self.uia_settings = result;
        },function(err){
            console.log(err);
        });

        smartcoins.then(function(result){
            console.log(result);
            sm_coins_obj = result;
            merchant_account = result.name
            self.data = result;
        },function(err){
            console.log(err);
        });
        
        reward_uia.then(function(result){
        	
            console.log(result);
            self.uia = result;
            
        },function(err){
            console.log(err);
        });
                
    },

    auto_back: true,

    show: function(){
        var self = this;
        this._super();
        
        this.$('.button.print').click(function(){
            if (!self._locked) {
                self.print();
            }
        });
        this.$('.back').click(function(){
            self.gui.back();
        });
        this.$('.coin-img').html('<img width="40px" src="../../smartcoins_pos/static/img/bts.png">')
        //this.print(); //Automatically print
        
        
        var order_obj = this.pos.get_order().export_for_printing();
        var line_items = [];
        var sum = 0;
        order_obj.orderlines.forEach(function(line_obj) {
            line_items.push({'label':line_obj.product_name, 'quantity':line_obj.quantity, 'price':line_obj.price_with_tax.toString()});
            sum = sum +(parseInt(line_obj.quantity) * parseFloat(line_obj.price_with_tax) );
        });
        var rps_title = "";
        if(self.uia_settings.amount > 0 && self.uia_settings.r_points > 0){
        	var rps_given = parseInt(sum / self.uia_settings.amount) * self.uia_settings.r_points;
        	rps_title = "You will earn " + rps_given + " reward points";
        	console.log('-----Rps Given: ', rps_title);
        }
        else{
        	console.log('-----Rps not found');
        }
        this.$('.smartcoin_name').html(rps_title);

        var oid = order_obj.name.split(' ');
        var callback_url = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '')+'/smartcoins_pos/smartcoins_transactions/'+oid[1]+'/';
        var string={
        	    "to": this.data.name,
        	    "to_label": order_obj.company.name,
        	    "currency": this.data.smartcoins.name,
        	    "memo": order_obj.name+" #blockpay",
        	    "line_items": line_items,
        	    "note": "Something the merchant wants to say to the user",
        	    "callback": callback_url,
        	    "ruia": self.uia != "" ? self.uia.uia.asset_id : ""  
        	};
	   localStorage.setItem("sm_coin_order_transaction", JSON.stringify(string));
        console.log(string);
        hash_generator(self,string);
        var intervalID = setInterval(function(){
        	console.log('-----start checking sm coin status');
        	self.check_transaction(intervalID,oid[1]);
        }, 5000);

    },
    check_transaction: function(intervalID,oid){
    	var self = this;
    	var transactions = new Model('smartcoins_pos.smartcoins_transactions').call('check_order_transaction', {order:oid});
    	transactions.then(function(result){
            if(!$.isEmptyObject(result)){
            	console.log('-----stopping interval');
        		clearInterval(intervalID);
        		localStorage.setItem("sm_coin_transaction_status", true);
        		self.gui.show_screen('payment');
        	}
        },function(err){
            console.log(err);
        });
    },
    generate_QR: function(hash){
    	console.log(hash);
    	self.$('.smartcoins-qr-container').html(""); //Emptying the container
    	self.$('.smartcoins-qr-container').qrcode({
    		text	: hash,
    		size: 400,
		    fill: '#006500',
		    // mode: 4,
		    // image: $('#img-buffer')[0],
    	});
    },
    lock_screen: function(locked) {
        this._locked = locked;
        if (locked) {
            this.$('.next').removeClass('highlight');
        } else {
            this.$('.next').addClass('highlight');
        }
    },
    print_web: function() {
        window.print();
    },
    print_xml: function() {
        var env = {
            widget:  this,
            pos:     this.pos,
            order:   this.pos.get_order(),
            receipt: this.pos.get_order().export_for_printing(),
            paymentlines: this.pos.get_order().get_paymentlines()
        };
        var receipt = QWeb.render('XmlReceipt',env);

        this.pos.proxy.print_receipt(receipt);
    },
    print: function() {
        var self = this;

        if (!this.pos.config.iface_print_via_proxy) { // browser (html) printing

            this.lock_screen(true);

            setTimeout(function(){
                self.lock_screen(false);
            }, 1000);

            this.print_web();
        } else {    // proxy (xml) printing
            //this.print_xml(); TODO: Modify function to print QR Code
            this.lock_screen(false);
        }
    },
    
});
/*--------------------------------------*\
|         THE Block Trade SMARTCOINS QR |
\*======================================*/

//The smartcoinsqr displays the QR code of smartcoins,
//and allows the cashier to make payment.

var BTSmartCoinsQRScreenWidget = ScreenWidget.extend({
   template: 'BTSmartCoinsQRScreenWidget',

   init: function(parent, options){
       this._super(parent, options);
       this.smartcoin_cache = new DomCache();
       var self = this;
   },

   auto_back: true,
   
   init_trade: function(data, wallet_type, amount){
	 var self = this;
     $.ajax({url: "https://blocktrades.us/api/v2/simple-api/initiate-trade",
		   type: "post",
		   data: data,
		   success: function(result){
			   var order_transaction = JSON.parse(localStorage.getItem("order_transaction"));
			   order_transaction["input_address"] = result.inputAddress;
			   localStorage.setItem("order_transaction", JSON.stringify(order_transaction));
			   var inputAddress = result.inputAddress;
			   generated_input_address = inputAddress;
			   var QrinputAddress = wallet_type + ":" + result.inputAddress + "?amount=" + amount;
			   self.generate_QR(QrinputAddress);
			   var myVar = setInterval(function(){ 
			   $.ajax({
				   url: "https://blocktrades.us/api/v2/simple-api/transactions?inputAddress=" +  inputAddress,
				   type: "get",
				   success : function(result){
					   console.log('------checking transaction status');
					   console.log(result)
					   var order_transaction = JSON.parse(localStorage.getItem("order_transaction"));
					   if(result.length && result[0].inputNumberOfConfirmations > 0){
						   stopTimer();
						   order_transaction["transaction_status"] = true;
						   localStorage.setItem("order_transaction", JSON.stringify(order_transaction));
						   self.gui.show_screen('payment');
					   }
				   }
				 });
			   }, 8000);
			   
			   function stopTimer(){
       			   console.log('----stop checking transaction status');
       			   clearInterval(myVar);
       		   }
			   
			   
		   }
	   });
   },
   
   show: function(){
       this._super();
       var self = this;
       $(".altcoin_name").html(bt_selected_coin_name);
       var img = "";
       	  if (bt_selected_coin_name.toLowerCase() == "dogecoin"){
       	  	  img = "doge.png";
       	  }else if (bt_selected_coin_name.toLowerCase() == "litecoin"){
       	  	  img = "ltc.png";
       	  }else if (bt_selected_coin_name.toLowerCase() == "bitshares"){
       	  	  img = "bts.png";
       	  }else if (bt_selected_coin_name.toLowerCase() == "dash"){
       	  	  img = "dash.png";
       	  }else if (bt_selected_coin_name.toLowerCase() == "nubits" || bt_selected_coin_name.toLowerCase() == "nushares"){
       	  	  img = "nbt.png";
       	  }else if (bt_selected_coin_name.toLowerCase() == "peercoin"){
       	  	  img = "ppc.png";
       	  }else {
       	      img = "bitcoin-logo.png";
       	  }
       this.$('.coin-img').html('<img width="40px" src="../../smartcoins_pos/static/img/'+img+'">')
       var order_obj = self.pos.get_order().export_for_printing();
       var sum = 0;
       order_obj.orderlines.forEach(function(line_obj) {
    	   sum = sum +(parseInt(line_obj.quantity) * parseFloat(line_obj.price_with_tax) );
       });
       
       var smartcoins = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_bt_data', {id:bt_coin_id, billing_amount:sum});
       
       smartcoins.then(function(result){
    	   console.log('--------on click bt coin data');
           console.log(result);
           self.data = result;
//           Get BTC amount from result
           var amount = result["estimated_amount"];
           var wallet_type = result["selected_alt_wallet_type"];
           var payment_str = "Please  Pay " + amount   + " " + result["selected_alt_coin_symbol"]
           self.$('.bt_smartcoin_name').html( payment_str );
           var data = {
        		   "inputCoinType": result["trading_pairs"]["input_coin_type"],
        		   "outputCoinType": result["trading_pairs"]["output_coin_type"],
        		   "outputAddress": merchant_account,
        		   "outputMemo": ""
        		 };
//           Initiate trade
           self.init_trade(data, wallet_type, amount);           
       },function(err){
           console.log(err);
       });
       

       this.$('.button.print.bt_button').click(function(){
           if (!self._locked) {
               self.print();
           }
       });
       this.$('.button.back.bt_back').click(function(){
           self.gui.back();
       });
       

   },
   generate_QR: function(hash){
   	console.log(hash);
   	self.$('.bt_smartcoins-qr-container').html(""); //Emptying the container
   	self.$('.bt_smartcoins-qr-container').qrcode({
   		text	: hash,
   		size: 400,
   	});
   },
   lock_screen: function(locked) {
       this._locked = locked;
       if (locked) {
           this.$('.next').removeClass('highlight');
       } else {
           this.$('.next').addClass('highlight');
       }
   },
   print_web: function() {
       window.print();
   },
   print_xml: function() {
       var env = {
           widget:  this,
           pos:     this.pos,
           order:   this.pos.get_order(),
           receipt: this.pos.get_order().export_for_printing(),
           paymentlines: this.pos.get_order().get_paymentlines()
       };
       var receipt = QWeb.render('XmlReceipt',env);

       this.pos.proxy.print_receipt(receipt);
   },
   print: function() {
       var self = this;

       if (!this.pos.config.iface_print_via_proxy) { // browser (html) printing

           this.lock_screen(true);

           setTimeout(function(){
               self.lock_screen(false);
           }, 1000);

           this.print_web();
       } else {    // proxy (xml) printing
           //this.print_xml(); TODO: Modify function to print QR Code
           this.lock_screen(false);
       }
   },
   
});

/*--------------------------------------*\
|         THE SMARTCOINS LIST              |
\*======================================*/

//The smartcoinslist displays the list of smartcoins,
//and allows the cashier to make payment.

var SmartCoinsListScreenWidget = ScreenWidget.extend({
   template: 'SmartCoinsListScreenWidget',

   init: function(parent, options){
       this._super(parent, options);
       this.smartcoin_cache = new DomCache();
       var self = this;
       var smartcoins = new Model('smartcoins_pos.smartcoins_pos').call('get_selected_bt_coins');

       smartcoins.then(function(result){
//    	   console.log('------get_selected_bt_coins method called-----');
           console.log(result);
           self.data = result;
       },function(err){
           console.log(err);
       });
       
   },

   auto_back: true,

   show: function(){
       var self = this;
       this._super();

       this.renderElement();

       this.$('.back').click(function(){
           self.gui.back();
       });

       this.render_list(this.data.smartcoins);
       
       this.$('.smartcoins-list-contents').delegate('.smartcoins-line','click',function(event){
//           self.line_select(event,$(this),parseInt($(this).data('id')));
    	   bt_coin_id = $(this).data('id');
    	   bt_selected_coin_name = $(this).children().text()
           self.gui.show_screen('bt_smartcoinsqr');
//           console.log(bt_coin_id);
       });
       
       var order_obj = this.pos.get_order().export_for_printing();
       var sum = 0;
       order_obj.orderlines.forEach(function(line_obj) {
           sum = sum +(parseInt(line_obj.quantity) * parseFloat(line_obj.price_with_tax) );
       });
       var order_transaction = JSON.parse(localStorage.getItem("order_transaction"));
	   order_transaction["amount"] = sum;
	   localStorage.setItem("order_transaction", JSON.stringify(order_transaction));

   },
   render_list: function(smartcoins){
       var contents = this.$el[0].querySelector('.smartcoins-list-contents');
       contents.innerHTML = "";
       for(var i = 0, len = Math.min(smartcoins.length,1000); i < len; i++){
           var smartcoin    = smartcoins[i];
           var smartcoinline = this.smartcoin_cache.get_node(smartcoin.id);
           if(!smartcoinline){
               var smartcoinline_html = QWeb.render('SmartCoinLine',{widget: this, smartcoin:smartcoins[i]});
               var smartcoinline = document.createElement('tbody');
               smartcoinline.innerHTML = smartcoinline_html;
               smartcoinline = smartcoinline.childNodes[1];
               this.smartcoin_cache.cache_node(smartcoin.id,smartcoinline);
           }
           if( smartcoins === this.new_client ){
               smartcoinline.classList.add('highlight');
           }else{
               smartcoinline.classList.remove('highlight');
           }
           contents.appendChild(smartcoinline);
       }
       this.$( ".smartcoins-line.paymentmethods" ).each(function( index ) {
       	  var td = $(this).find("td");
       	  var img = "";
       	  if (td.html().toLowerCase() == "dogecoin"){
       	  	  img = "doge.png";
       	  }else if (td.html().toLowerCase() == "litecoin"){
       	  	  img = "ltc.png";
       	  }else if (td.html().toLowerCase() == "bitshares"){
       	  	  img = "bts.png";
       	  }else if (td.html().toLowerCase() == "dash"){
       	  	  img = "dash.png";
       	  }else if (td.html().toLowerCase() == "nubits" || td.html().toLowerCase() == "nushares"){
       	  	  img = "nbt.png";
       	  }else if (td.html().toLowerCase() == "peercoin"){
       	  	  img = "ppc.png";
       	  }else {
       	      img = "bitcoin-logo.png";
       	  }
		  td.css('background-image','url(../../smartcoins_pos/static/img/'+img+')');
		  td.css('background-repeat','no-repeat');
		  td.css('background-size','4em');
		  td.css('background-position-y','center');
		  td.css('background-position-x','20px');
	   });
   },
   save_changes: function(){
       if( this.has_client_changed() ){
           this.pos.get_order().set_client(this.new_client);
       }
   },
});

gui.define_screen({name:'smartcoinslist', widget: SmartCoinsListScreenWidget});
gui.define_screen({name:'smartcoinsqr', widget: SmartCoinsQRScreenWidget});
gui.define_screen({name:'bt_smartcoinsqr', widget: BTSmartCoinsQRScreenWidget});


});
