import hashlib
import datetime
import functools
import unittest

import api


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                print('Requests args {}'.format(new_args))
                f(*new_args)
        return wrapper
    return decorator


class TestSuite(unittest.TestCase):

    @cases(["asd",
            79175002040,
            'asd@asd.ru',
            ])
    def test_field(self, param):
        '''
        Проверка поля родителя - Field
        :return: Что ввели, то получили.
        '''
        f = api.Field()
        self.assertEqual(f.parse_validate(param), param)

    @cases(["asd",
            'asd@asd.ru',
            '123!@#asdd'
            ])
    def test_charfield(self, param):
        f = api.CharField()
        self.assertEqual(f.parse_validate(param), param)


    @cases([-1,
            1234,
           1.2,
            [1,2,3],
            {'a': 123}])
    def test_non_charfield(self, param):
        f = api.CharField()
        with self.assertRaises(ValueError):
            f.parse_validate(param)

    @cases([
            {'a': 123}])
    def test_argumentfield(self, param):
        f = api.ArgumentsField()
        self.assertEqual(type(f.parse_validate(param)), dict)

    @cases([-1,
            1234,
           1.2,
            [1, 2, 3]
            ])
    def test_non_argumentfield(self, param):
        f = api.ArgumentsField()
        with self.assertRaises(ValueError):
            f.parse_validate(param)

    @cases(['asd@asd.ru',
            '@'])
    def test_emailfield(self, email):
        f = api.EmailField()
        self.assertEqual(f.parse_validate(email), email)

    @cases([-1,
            1234,
           1.2,
            [1, 2, 3]
            ])
    def test_non_emailfield(self, param):
        f = api.EmailField()
        with self.assertRaises(ValueError):
            f.parse_validate(param)

    @cases(["79175002040",
            79175002040])
    def test_phonefield(self, phone):
        f = api.PhoneField()
        self.assertEqual(f.parse_validate(phone), phone)

    @cases([89175002040,
            '89175002040',
            'asd',
            2312])
    def test_non_phonefield(self, phone):
        f = api.PhoneField()
        with self.assertRaises(ValueError):
            f.parse_validate(phone)

    @cases(['27.02.2009',
            '02.03.2019',])
    def test_datefield(self, datefield):
        f = api.DateField()
        dt = datetime.datetime.strptime(datefield, "%d.%m.%Y")
        self.assertEqual(f.parse_validate(datefield), dt)

    @cases(['27.02.09',
            '02.27.2009',
            '13/11/2020',
            122233,
            'asd'])
    def test_not_datefield(self, datefield):
        f = api.DateField()
        with self.assertRaises(ValueError):
            f.parse_validate(datefield)

    @cases(['27.02.2009',
            '02.06.2009'])
    def test_birthday(self, birthday):
        f = api.BirthDayField()
        dt = datetime.datetime.strptime(birthday, "%d.%m.%Y")
        self.assertEqual(f.parse_validate(birthday), dt)

    @cases(['27/02/2009',
            '02.27.2009',
            '02.02.1878',
            12122009])
    def test_non_birthday(self, birthday):
        f = api.BirthDayField()
        with self.assertRaises(ValueError):
            f.parse_validate(birthday)

    @cases([1,
            2,
            0])
    def test_genderfield(self, gendernum):
        f = api.GenderField()
        self.assertEqual(type(f.parse_validate(gendernum)), str)
        self.assertEqual(f.parse_validate(gendernum), str(gendernum))

    @cases([4,
            '1',
            -1])
    def test_not_genderfield(self, gendernum):
        f = api.GenderField()
        with self.assertRaises(ValueError):
            f.parse_validate(gendernum)

    @cases([[1, 2, 3],
            [i for i in range(5)]
            ])
    def test_clientid(self, clientid):
        f = api.ClientIDsField()
        self.assertEqual(type(f.parse_validate(clientid)), list)
        for cid in clientid:
            self.assertEqual(type(cid), int)

    @cases([{1, 2, 3},
            [-1, 6],
            [1.1,.2],
            ])
    def test_non_clientid(self, clientid):
        f = api.ClientIDsField()
        with self.assertRaises(ValueError):
            f.parse_validate(clientid)


if __name__ == "__main__":
    unittest.main()