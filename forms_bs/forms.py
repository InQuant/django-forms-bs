from django import forms
from django.forms import CheckboxInput, RadioSelect
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class BSForm(forms.Form):
    def __str__(self):
        return self.as_bootstrap()

    def as_bootstrap(self):
        return self._bs_html_output(
            normal_row='<div class="form-group" %(html_class_attr)s>%(label)s%(field)s%(help_text)s%(errors)s</div>',
            error_row='<div class="invalid-feedback">%s</div>',
            row_ender='</div>',
            help_text_html='<small class="form-text text-muted">%s</small>',
            checkbox_row='<div class="form-check" %(html_class_attr)s>%(field)s%(label)s%(help_text)s%(errors)s</div>',
        )

    def _bs_html_output(self, normal_row, error_row, row_ender, help_text_html, checkbox_row):
        """Output HTML. Used by as_bootstrap()"""
        # Errors that should be displayed above all fields.
        top_errors = self.non_field_errors().copy()
        output, hidden_fields = [], []

        for name, field in self.fields.items():
            html_class_attr = ''
            bf = self[name]
            bf_errors = self.error_class(bf.errors)
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend(
                        [_('(Hidden field %(name)s) %(error)s') % {'name': name, 'error': str(e)}
                         for e in bf_errors])
                hidden_fields.append(str(bf))
            else:
                # Create a 'class="..."' attribute if the row should have any
                # CSS classes applied.
                css_classes = bf.css_classes()
                if css_classes:
                    html_class_attr = ' class="%s"' % css_classes

                if bf.label:
                    label = conditional_escape(bf.label)
                    label = bf.label_tag(label) or ''
                else:
                    label = ''

                if field.help_text:
                    help_text = help_text_html % field.help_text
                else:
                    help_text = ''

                html_errors = ''
                for error in bf_errors:
                    html_errors += error_row % error

                # add default bs class
                bf_class = bf.field.widget.attrs.get('class', '')

                # set up checkbox field
                is_checkbox = False
                if bf.field.widget.input_type == CheckboxInput.input_type:
                    bf.field.widget.attrs['class'] = str(bf_class + ' form-check-input').strip()
                    label = bf.label_tag(bf.label, label_suffix='test') or ''
                    is_checkbox = True

                elif bf.field.widget.input_type == RadioSelect.input_type:
                    # TODO: Needs to be displayed better via widget changes
                    pass
                else:
                    bf.field.widget.attrs['class'] = str(bf_class + ' form-control').strip()

                if bf_errors:
                    bf.field.widget.attrs['class'] += ' is-invalid'
                _data = {
                    'errors': html_errors,
                    'label': label,
                    'field': bf,
                    'help_text': help_text,
                    'html_class_attr': html_class_attr,
                    'css_classes': css_classes,
                    'field_name': bf.html_name,
                }

                _html = normal_row % _data if not is_checkbox else checkbox_row % _data
                output.append(_html)

        if top_errors:
            output.insert(0, error_row % top_errors)

        if hidden_fields:  # Insert any hidden fields in the last row.
            html_class_attr = ''
            str_hidden = ''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {
                        'errors': '',
                        'label': '',
                        'field': '',
                        'help_text': '',
                        'html_class_attr': html_class_attr,
                        'css_classes': '',
                        'field_name': '',
                    })
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe('\n'.join(output))

