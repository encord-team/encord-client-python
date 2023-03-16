import pytest

from encord.objects.frames import frames_class_to_frames_list, Range


def test_frames_class_to_frames_list():
    # Single frame
    assert frames_class_to_frames_list(1) == [1]
    assert frames_class_to_frames_list(10) == [10]

    # Range
    assert frames_class_to_frames_list(Range(1, 4)) == [1, 2, 3, 4]
    assert frames_class_to_frames_list(Range(0, 1)) == [0, 1]
    assert frames_class_to_frames_list(Range(4, 4)) == [4]

    # List of Range
    list_of_range_1 = [Range(2, 3), Range(3, 5), Range(7, 7)]
    assert frames_class_to_frames_list(list_of_range_1) == [2, 3, 4, 5, 7]
    list_of_range_2 = [Range(10, 12), Range(3, 5), Range(8, 9), Range(8, 9)]
    assert frames_class_to_frames_list(list_of_range_2) == [3, 4, 5, 8, 9, 10, 11, 12]

    # List of integer frame numbers
    # Empty List
    assert frames_class_to_frames_list([]) == []
    list_of_integers_1 = [4, 5, 6, 24, 60]
    assert frames_class_to_frames_list(list_of_integers_1) == list_of_integers_1
    assert frames_class_to_frames_list([4]) == [4]
    assert frames_class_to_frames_list([9, 8, 7]) == [7, 8, 9]
    assert frames_class_to_frames_list([9, 2, 4, 4, 14]) == [2, 4, 9, 14]

    # Exception
    with pytest.raises(RuntimeError):
        frames_class_to_frames_list([4, Range(4, 6)])
    with pytest.raises(RuntimeError):
        frames_class_to_frames_list({3, 5, 7})
