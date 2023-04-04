# models.py (plastics_eol)
# !/usr/bin/env python3
# coding=utf-8

"""Definition of models."""

from django.db import models
from django.urls import reverse
from django.utils import timezone
from .constants import *
from accounts.models import User
from plastics_eol import constants as CONST


class Scenario(models.Model):
    """Class representing a calculator scenario."""

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(blank=False, null=False,
                                default=timezone.now)
    name = models.TextField(blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse('scenario_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class Condition(models.Model):
    """User inputs for calculator Conditions (in fractions)."""
    scenario = models.OneToOneField(Scenario,
                                    on_delete=models.CASCADE,
                                    primary_key=True)
    total_msw = models.FloatField(null=False, blank=False, default=0.0)
    total_waste = models.FloatField(null=False, blank=False, default=0.0)
    total_recyc = models.FloatField(null=False, blank=False, default=0.0)
    domestic_recyc = models.FloatField(null=False, blank=False, default=0.0)
    export = models.FloatField(null=False, blank=False, default=0.0)
    re_export = models.FloatField(null=False, blank=False, default=0.0)
    recyc_efficiency = models.FloatField(null=False, blank=False, default=0.0)
    incinerated = models.FloatField(null=False, blank=False, default=0.0)
    landfilled = models.FloatField(null=False, blank=False, default=0.0)
    waste_facility_emissions = models.FloatField(null=False,
                                                 blank=False,
                                                 default=0.0)
    landfill_emissions = models.FloatField(null=False,
                                           blank=False,
                                           default=0.0)


class MSWGeneric(models.Model):
    """Generic fields shared with most MSW User Specification classes."""
    scenario = models.OneToOneField(Scenario,
                                    on_delete=models.CASCADE,
                                    primary_key=True)
    inorganic = models.FloatField(null=False, blank=False, default=0.0)
    other = models.FloatField(null=False, blank=False, default=0.0)
    yard_trimmings = models.FloatField(null=False, blank=False, default=0.0)
    food = models.FloatField(null=False, blank=False, default=0.0)
    rubber_leather_textiles = models.FloatField(null=False,
                                                blank=False,
                                                default=0.0)
    wood = models.FloatField(null=False, blank=False, default=0.0)
    metals = models.FloatField(null=False, blank=False, default=0.0)
    glass = models.FloatField(null=False, blank=False, default=0.0)
    paper = models.FloatField(null=False, blank=False, default=0.0)
    plastics = models.FloatField(null=False, blank=False, default=0.0)

    class Meta:
        abstract = True

    def multiply_mass(self, mass):
        totals = self.__dict__
        values = [totals[w] for w in CONST.WASTE_TYPES]
        # for key in self build dict
        # totals['key'] = self.total_mass * self.key
        fraction_mass = dict(zip(CONST.WASTE_TYPES, map(lambda x: x*mass, values)))
        return fraction_mass


class MSWTotalsGeneric(MSWGeneric):
    """User Specifications for MSW Data."""
    total_mass = models.FloatField(null=False, blank=False, default=0.0)

    class Meta:
        abstract = True

    def fractions_to_mass(self):
        return self.multiply_mass(self.total_mass)


class MSWComposition(MSWTotalsGeneric):
    """User specifications for Municipal Solid Waste Composition."""


class MSWRecycling(MSWTotalsGeneric):
    """User Specifications for Recycling Data."""


class MSWIncineration(MSWTotalsGeneric):
    """User Specifications for Incineration Data."""


class MSWLandfill(MSWTotalsGeneric):
    """User Specifications for Landfill Data."""


class MSWCompost(MSWTotalsGeneric):
    """User Specifications for Compost Data."""


class PlasticGeneric(models.Model):
    """Generic fields shared with most Plastic User Specification classes."""
    scenario = models.OneToOneField(Scenario,
                                    on_delete=models.CASCADE,
                                    primary_key=True)
    pet = models.FloatField(null=False, blank=False, default=0.0)
    hdpe = models.FloatField(null=False, blank=False, default=0.0)
    pvc = models.FloatField(null=False, blank=False, default=0.0)
    ldpe = models.FloatField(null=False, blank=False, default=0.0)
    pla = models.FloatField(null=False, blank=False, default=0.0)
    pp = models.FloatField(null=False, blank=False, default=0.0)
    ps = models.FloatField(null=False, blank=False, default=0.0)
    other = models.FloatField(null=False, blank=False, default=0.0)

    class Meta:
        abstract = True


class PlasticRecycling(PlasticGeneric):
    """User Specifications for Plastic Recycled Proportions (fractions)"""


class PlasticIncineration(PlasticGeneric):
    """User Specifications for Plastic Incinerated Proportions (fractions)"""


class PlasticLandfill(PlasticGeneric):
    """User Specifications for Plastic Landfilled Proportions (fractions)"""


class PlasticReportedRecycled(PlasticGeneric):
    """User Specifications for Plastic Reported Recycled Masses (tons)"""


class ImportExportGeneric(models.Model):
    """
    Generic fields shared with most
    Plastic Import/Export User Specification classes.
    """
    scenario = models.OneToOneField(Scenario,
                                    on_delete=models.CASCADE,
                                    primary_key=True)
    ethylene = models.FloatField(null=False, blank=False, default=0.0)
    vinyl_chloride = models.FloatField(null=False, blank=False, default=0.0)
    styrene = models.FloatField(null=False, blank=False, default=0.0)
    other = models.FloatField(null=False, blank=False, default=0.0)

    class Meta:
        abstract = True


class ImportedPlastic(ImportExportGeneric):
    """User Specifications for Plastic Imported Masses."""


class ExportedPlastic(ImportExportGeneric):
    """User Specifications for Plastic Exported Masses."""


class ReExportedPlastic(ImportExportGeneric):
    """User Specifications for Plastic Re-Exported Masses."""


class Stream(models.Model):
    """Class representing a Stream from the calculator."""
    # (1, Monomer/Raw Materials)
    id = models.IntegerField(null=False, primary_key=True)
    title = models.TextField(blank=False, null=False)

class Result(models.Model):
    """Results for a calculator run."""
    # (auto_id, 1, 1, PET, 4624952)
    scenario = models.OneToOneField(Scenario, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, null=True, on_delete=models.SET_NULL)
    key = models.TextField(blank=False, null=False) # i.e. PET,
    value = models.FloatField(null=False) # i.e. 4,624,952

    def __str__(self, *args, **kwargs):
        """Override stringify method to return <.5 etc. when appropriate."""
        if self.value < 0.1:
            return '<0.1'
        elif self.value < 0.5:
            return '<0.5'
        elif self.value < 1:
            return '<1'
        # TODO Could consider formatting it with commas, etc.
        return str(self.value)
