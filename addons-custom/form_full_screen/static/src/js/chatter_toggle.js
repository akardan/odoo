/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { append, createElement, setAttributes } from "@web/core/utils/xml";
import { FormCompiler } from "@web/views/form/form_compiler";

patch(FormCompiler.prototype, {

    compile(node, params) {
        const res = super.compile(node, params);
        const chatterContainerHookXml = res.querySelector(".o-mail-Form-chatter");
        if (!chatterContainerHookXml) {
            return res; // no chatter, keep the result as it is
        }
        var statusbar = res.querySelector(".o_form_sheet_bg .o_form_statusbar");
        if (!statusbar){
            var o_form_sheet_bg = res.querySelector(".o_form_sheet_bg");
            var o_form_statusbar = createElement("div", {
                class: "o_form_statusbar position-relative d-flex justify-content-between mb-0 mb-md-2 pb-2 pb-md-0"
            });
            var o_form_div = createElement("div", {class: "me-auto"});
            append(o_form_statusbar, o_form_div);
            o_form_sheet_bg.prepend(o_form_statusbar);
            var statusbar = res.querySelector(".o_form_sheet_bg .o_form_statusbar");
        }
        if (statusbar) {
            const webClientViewAttachmentViewHookXml = res.querySelector(".o_attachment_preview");
            const hasPreview = !!webClientViewAttachmentViewHookXml;
            var HideChatter = createElement("button");
            setAttributes(HideChatter, { "type": "button",
                "t-attf-class": `{{ ["SIDE_CHATTER", "EXTERNAL_COMBO_XXL"].includes(__comp__.mailLayout(${hasPreview})) ? "btn btn-secondary o_chatter_toggle_btn ms-1" : "d-none" }}`,
                "data-collapsed": false,
            });
            var span = createElement("span");
            append(HideChatter, span);
            function toggleChatter(e) {
                const target = e.target.closest('.o_chatter_toggle_btn');
                if (target && document.contains(target)) {
                    target.dataset.collapsed = !JSON.parse(target.dataset.collapsed)
                    document.getElementsByClassName('o_form_sheet_bg')[0].classList.toggle('max-width-unset');
                    document.getElementsByClassName('o-mail-ChatterContainer')[0].classList.toggle('d-none');
                }
            }
            if (!document.__chatterClickBound) {
                document.addEventListener('click', toggleChatter);
                document.__chatterClickBound = true;
            }
            append(statusbar, HideChatter);
        }
        return res;
    },
})