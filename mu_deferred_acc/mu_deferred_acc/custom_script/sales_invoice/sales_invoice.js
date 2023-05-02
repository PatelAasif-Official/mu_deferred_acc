frappe.ui.form.on("Sales Invoice",{
    refresh:function(frm){
        if (frm.doc.docstatus==1){
            frm.add_custom_button(__("Process Deferred Revenue"), function(){
                frappe.model.open_mapped_doc({
                    method: "mu_deferred_acc.mu_deferred_acc.utils.process_dr",
                    frm: cur_frm
                })
            },);

        }
    },

})


