# frequently used constants for application


LEVEL_CHOICES = (
    ('Country', 'Country'), ('State', 'State'), ('District', 'District'),
    ('Taluk', 'Taluk'), ('Mandal', 'Mandal'),
    ('GramaPanchayath', 'GramaPanchayath'),
    ('Village', 'Village'),
)
# Level Choices

levels = [u'Country',
          u'State',
          u'District',
          u'Taluk',
          u'Mandal',
          u'GramaPanchayath',
          u'Village'
]
# Levels

OPTIONAL = {'blank': True, 'null': True}
# Specify that field is nullabel
# use **OPTIONAL in models


data = {}
# Mutilate data and import anywhere
