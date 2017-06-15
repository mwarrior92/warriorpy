# list with modulo indices
class looplist(list):
    def __getitem__(self, item):
        list_len = len(self)
        m_item = item % list_len
        tmp_list = list(self)
        return tmp_list[m_item]
