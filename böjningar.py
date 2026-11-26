from functools import partial


class Tempus():
    def __init__(self, förälder, förälderattribut):
        self.tempus = None
        self.förälder = förälder
        self.förälderattribut = förälderattribut

    def skapa_tempus(self, tempus):
        self.tempus = tempus
        setattr(self.förälder, self.förälderattribut, tempus)
        return self.förälder

    def generera_dict(self):
        tempus_dict = {}

        tempus_dict['infinitiv'] = (None, partial(self.skapa_tempus, 'infinitiv'))
        tempus_dict['presens'] = (None, partial(self.skapa_tempus, 'presens'))
        tempus_dict['preteritum'] = (None, partial(self.skapa_tempus, 'preteritum'))
        tempus_dict['perfekt'] = (None, partial(self.skapa_tempus, 'perfekt'))
        tempus_dict['supinum'] = (None, partial(self.skapa_tempus, 'supinum'))
        tempus_dict['imperativ'] = (None, partial(self.skapa_tempus, 'imperativ'))
        tempus_dict['perfekt particip'] = (None, partial(self.skapa_tempus, 'perfekt particip'))
        tempus_dict['presens particip'] = (None, partial(self.skapa_tempus, 'presens particip'))

        return tempus_dict