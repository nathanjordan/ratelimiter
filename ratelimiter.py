import unittest
import mock
from datetime import datetime, timedelta
from functools import wraps


class RateLimitException(Exception):
    """Exception raised when rate limit reached."""
    pass


def _current_time():
    """Function that returns the current time.

    Abstracted for testing purposes.
    """
    return datetime.now()


def _limit_reached(queue, time, rate, period):
    """Returns if the rate limit has been reached given a queue.

    :param queue: The queue of time stamps.
    :type queue: list
    :param time: the current time.
    :type time: `datetime.datetime`
    :param rate: The amount of requests permitted.
    :type rate: int
    :param period: The time window for the rate.
    :type period: `datetime.timedelta`
    :returns: Whether the limit has been reached
    :rtype: bool

    """
    # remove all the expired timestamps
    for k in range(0, len(queue)):
        # pop the old value off
        i = queue.pop()
        # if the time is greater than now, re-add it and stop looping
        if i >= time - period:
            queue.insert(0, i)
            break
    # return if the queue has more values than the rate
    return len(queue) >= rate


def limiter(rate, per):
    """A decorator for a rate limited function.

    :param rate: The amount of requests permitted.
    :type rate: int
    :param per: The time window for the rate (eg. minute, hour, etc.)
    :type period: `datetime.timedelta`
    """
    
    def wrap(f):
        # create an empty queue
        queue = []
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            # if the limit has been reached, raise
            if _limit_reached(queue, _current_time(), rate, per):
                raise RateLimitException
            # otherwise, add the current time to the queue
            queue.append(_current_time())
            # call the function
            return f(*args, **kwargs)
        return wrapped
    return wrap


class TestRateLimiter(unittest.TestCase):
    """Test case for rate limiter decorator."""

    def setUp(self):

        @limiter(rate=3, per=timedelta(minutes=1))
        def test_func():
            """Test rate limited function."""
            pass

        self.test_func = test_func

    @mock.patch('__main__._current_time', autospec=True)
    def test_not_rate_limited(self, mock_time):
        mock_time.return_value = datetime.now()
        self.test_func()
        self.test_func()
        self.test_func()

    @mock.patch('__main__._current_time', autospec=True)
    def test_rate_limited(self, mock_time):
        mock_time.return_value = datetime.now()
        with self.assertRaises(RateLimitException):
            self.test_func()
            self.test_func()
            self.test_func()
            self.test_func()

    @mock.patch('__main__._current_time', autospec=True)
    def test_not_rate_limited_after(self, mock_time):
        current_time = datetime.now()
        mock_time.return_value = current_time
        with self.assertRaises(RateLimitException):
            self.test_func()
            self.test_func()
            self.test_func()
            self.test_func()
        mock_time.return_value = current_time + timedelta(minutes=2)
        self.test_func()
        self.test_func()
        self.test_func()


if __name__ == "__main__":
    unittest.main()
