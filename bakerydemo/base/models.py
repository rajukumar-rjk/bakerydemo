from __future__ import unicode_literals

from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register)
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel,
    PageChooserPanel, StreamFieldPanel,
)
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Collection, Orderable, Page
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.models import register_snippet

from .blocks import BaseStreamBlock


@register_snippet
class People(ClusterableModel):
    first_name = models.CharField("First name", max_length=254)
    last_name = models.CharField("Last name", max_length=254)
    job_title = models.CharField("Job title", max_length=254)

    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        FieldPanel('first_name', classname="col6"),
        FieldPanel('last_name', classname="col6"),
        FieldPanel('job_title'),
        ImageChooserPanel('image')
    ]

    search_fields = Page.search_fields + [
        index.SearchField('first_name'),
        index.SearchField('last_name'),
    ]

    @property
    def thumb_image(self):
        # fail silently if there is no profile pic or the rendition file can't
        # be found. Note @richbrennan worked out how to do this...
        try:
            return self.image.get_rendition('fill-50x50').img_tag()
        except:
            return ''

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'People'


@register_snippet
class FooterText(models.Model):
    body = RichTextField()

    panels = [
        FieldPanel('body'),
    ]

    def __str__(self):
        return "Footer text"

    class Meta:
        verbose_name_plural = 'Footer Text'


class AboutLocationRelationship(Orderable, models.Model):
    """
    This defines the relationship between the `LocationPage` within the `locations`
    app and the About page below allowing us to add locations to the about
    section.
    """
    page = ParentalKey(
        'AboutPage', related_name='location_about_relationship'
    )
    locations = models.ForeignKey(
        'locations.LocationPage', related_name='about_location_relationship'
    )
    panels = [
        PageChooserPanel('locations')
    ]


class AboutPage(Page):
    """
    The About Page
    """
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Location image'
    )

    body = StreamField(
        BaseStreamBlock(), verbose_name="About page detail", blank=True
    )
    # We've defined the StreamBlock() within blocks.py that we've imported on
    # line 12. Defining it in a different file gives us consistency across the
    # site, though StreamFields _can_ be created on a per model basis if you
    # have a use case for it

    content_panels = Page.content_panels + [
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        InlinePanel(
            'location_about_relationship',
            label='Locations',
            min_num=None
        ),
    ]

    # parent_page_types = [
    #    'home.HomePage'
    # ]

    # Defining what content type can sit under the parent
    # The empty array means that no children can be placed under the
    # LocationPage page model
    subpage_types = []

    # api_fields = ['image', 'body']


class HomePage(Page):
    """
    The Home Page
    """
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Location image'
    )

    body = StreamField(
        BaseStreamBlock(), verbose_name="Home page detail", blank=True
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
    ]

    def __str__(self):
        return self.title


class GalleryPage(Page):
    """
    This is a page to list all the locations on the site
    """
    choices = models.ForeignKey(
        Collection,
        limit_choices_to=~models.Q(name__in=['Root']),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Location listing image'
    )

    introduction = models.TextField(
        help_text='Text to describe the index page',
        blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('choices'),
        ImageChooserPanel('image'),
        FieldPanel('introduction')
    ]

    # parent_page_types = [
    #     'home.HomePage'
    # ]

    # Defining what content type can sit under the parent. Since it's a blank
    # array no subpage can be added
    subpage_types = [
    ]

    # api_fields = ['introduction']


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', related_name='form_fields')


class FormPage(AbstractEmailForm):
    header_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    body = StreamField(BaseStreamBlock())
    thank_you_text = RichTextField(blank=True)
    content_panels = AbstractEmailForm.content_panels + [
        ImageChooserPanel('header_image'),
        StreamFieldPanel('body'),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]


class PeopleModelAdmin(ModelAdmin):
    model = People
    menu_label = 'People'  # ditch this to use verbose_name_plural from model
    menu_icon = 'fa-people'  # change as required
    list_display = ('first_name', 'last_name', 'job_title', 'thumb_image')


class MyModelAdminGroup(ModelAdminGroup):
    menu_label = 'WagtailBakery'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (PeopleModelAdmin,)


# When using a ModelAdminGroup class to group several ModelAdmin classes together,
# you only need to register the ModelAdminGroup class with Wagtail:
modeladmin_register(MyModelAdminGroup)