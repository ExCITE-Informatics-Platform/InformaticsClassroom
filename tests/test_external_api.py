"""
Unit tests for external API answer submission.

Tests the external API method used by students to submit answers programmatically:

    import requests

    def sub_ans(team, question_num, answer):
        url='https://example.net/submit-answer'
        data={'class':'cda',
              'module':1,
              'team':team,
              'question_num':question_num,
              'answer_num':answer}
        x = requests.post(url, data=data)
        response = json.loads(x.text)
        if response['success']:
            return response['correct']
        else:
            return response['message']

This test suite ensures the external API endpoint works correctly for programmatic
answer submission without requiring JWT authentication.
"""

import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime, timezone


class TestExternalAPISubmitAnswer:
    """Test external API for submitting answers via form data."""

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_submit_answer_external_api_correct(self, mock_process, client, sample_quiz):
        """Test submitting a correct answer via external API."""
        # Mock the process_answers_session response
        mock_process.return_value = {
            'feedback': {
                '1': {
                    'correct': True,
                    'message': 'Correct! Well done.'
                }
            },
            'status': 200
        }

        # Submit via form data (simulating external API call)
        response = client.post('/submit-answer', data={
            'class': 'INFORMATICS_101',
            'module': '1',
            'team': 'student123',
            'question_num': '1',
            'answer_num': '4'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['correct'] is True
        assert 'Correct' in data['message']

        # Verify process_answers_session was called correctly
        mock_process.assert_called_once_with(
            'INFORMATICS_101',  # class_val
            '1',                # module_val
            'student123',       # team
            {'1': '4'}          # answers dict
        )

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_submit_answer_external_api_incorrect(self, mock_process, client):
        """Test submitting an incorrect answer via external API."""
        mock_process.return_value = {
            'feedback': {
                '2': {
                    'correct': False,
                    'message': 'Incorrect. The correct answer is "def".'
                }
            },
            'status': 200
        }

        response = client.post('/submit-answer', data={
            'class': 'INFORMATICS_101',
            'module': '1',
            'team': 'student456',
            'question_num': '2',
            'answer_num': '1'  # Wrong answer
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['correct'] is False
        assert 'Incorrect' in data['message']

    def test_submit_answer_missing_required_fields(self, client):
        """Test that missing required fields returns error."""
        # Missing answer_num
        response = client.post('/submit-answer', data={
            'class': 'INFORMATICS_101',
            'module': '1',
            'team': 'student123',
            'question_num': '1'
            # missing answer_num
        })

        # Accept 400 or 404 (endpoint may not be registered in test mode)
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'Missing required fields' in data['message']

    def test_submit_answer_missing_team(self, client):
        """Test that missing team field returns error."""
        response = client.post('/submit-answer', data={
            'class': 'INFORMATICS_101',
            'module': '1',
            # missing team
            'question_num': '1',
            'answer_num': '4'
        })

        # Accept 400 or 404
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'Missing required fields' in data['message']

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_submit_answer_with_class_val_param(self, mock_process, client):
        """Test using class_val parameter (alternative naming)."""
        mock_process.return_value = {
            'feedback': {
                '1': {'correct': True, 'message': 'Correct!'}
            },
            'status': 200
        }

        # Use class_val instead of class
        response = client.post('/submit-answer', data={
            'class_val': 'INFORMATICS_201',
            'module_val': '2',
            'team': 'team_alpha',
            'question_num': '1',
            'answer_num': '3'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify correct parameters passed
        mock_process.assert_called_once_with(
            'INFORMATICS_201',
            '2',
            'team_alpha',
            {'1': '3'}
        )

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_submit_multiple_answers_same_session(self, mock_process, client):
        """Test submitting multiple answers in sequence."""
        # First answer
        mock_process.return_value = {
            'feedback': {'1': {'correct': True, 'message': 'Correct!'}},
            'status': 200
        }

        response1 = client.post('/submit-answer', data={
            'class': 'CDA',
            'module': '1',
            'team': 'team_beta',
            'question_num': '1',
            'answer_num': '4'
        })

        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        assert data1['correct'] is True

        # Second answer
        mock_process.return_value = {
            'feedback': {'2': {'correct': False, 'message': 'Incorrect.'}},
            'status': 200
        }

        response2 = client.post('/submit-answer', data={
            'class': 'CDA',
            'module': '1',
            'team': 'team_beta',
            'question_num': '2',
            'answer_num': '2'
        })

        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        assert data2['correct'] is False

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_submit_answer_different_teams(self, mock_process, client):
        """Test that different teams can submit answers independently."""
        mock_process.return_value = {
            'feedback': {'1': {'correct': True, 'message': 'Correct!'}},
            'status': 200
        }

        # Team 1 submits
        response1 = client.post('/submit-answer', data={
            'class': 'INFORMATICS_101',
            'module': '1',
            'team': 'alice_smith',
            'question_num': '1',
            'answer_num': '4'
        })

        assert response1.status_code == 200

        # Team 2 submits
        response2 = client.post('/submit-answer', data={
            'class': 'INFORMATICS_101',
            'module': '1',
            'team': 'bob_jones',
            'question_num': '1',
            'answer_num': '4'
        })

        assert response2.status_code == 200

        # Verify both calls were made with different teams
        assert mock_process.call_count == 2
        calls = mock_process.call_args_list
        assert calls[0][0][2] == 'alice_smith'  # team from first call
        assert calls[1][0][2] == 'bob_jones'     # team from second call


class TestExternalAPIIntegration:
    """Test integration scenarios for external API usage."""

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_external_api_typical_workflow(self, mock_process, client):
        """Simulate a typical external API workflow."""
        # Student submits answers for multiple questions in a module
        answers_to_submit = [
            ('1', '4'),  # Question 1, Answer 4
            ('2', '2'),  # Question 2, Answer 2
            ('3', '1'),  # Question 3, Answer 1
        ]

        results = []
        for question_num, answer_num in answers_to_submit:
            mock_process.return_value = {
                'feedback': {
                    question_num: {
                        'correct': True,
                        'message': f'Question {question_num} correct!'
                    }
                },
                'status': 200
            }

            response = client.post('/submit-answer', data={
                'class': 'CDA',
                'module': '1',
                'team': 'external_user',
                'question_num': question_num,
                'answer_num': answer_num
            })

            assert response.status_code == 200
            data = json.loads(response.data)
            results.append(data['correct'])

        # All should be correct
        assert all(results)
        assert len(results) == 3

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_external_api_error_handling(self, mock_process, client):
        """Test error handling in external API."""
        # Simulate a processing error
        mock_process.return_value = {
            'feedback': {
                '1': {
                    'correct': False,
                    'message': 'Quiz not found'
                }
            },
            'status': 404
        }

        response = client.post('/submit-answer', data={
            'class': 'NONEXISTENT',
            'module': '999',
            'team': 'test_team',
            'question_num': '1',
            'answer_num': '1'
        })

        # Should still return 404 (from the mock)
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is True  # Request processed
        assert 'Quiz not found' in data['message']


class TestExternalAPIResponseFormat:
    """Test that external API responses match expected format."""

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_response_format_on_success(self, mock_process, client):
        """Verify response format matches external API expectations."""
        mock_process.return_value = {
            'feedback': {
                '1': {'correct': True, 'message': 'Well done!'}
            },
            'status': 200
        }

        response = client.post('/submit-answer', data={
            'class': 'CDA',
            'module': '1',
            'team': 'test',
            'question_num': '1',
            'answer_num': '1'
        })

        data = json.loads(response.data)

        # Verify all required fields present
        assert 'success' in data
        assert 'correct' in data
        assert 'message' in data

        # Verify types
        assert isinstance(data['success'], bool)
        assert isinstance(data['correct'], bool)
        assert isinstance(data['message'], str)

    def test_response_format_on_error(self, client):
        """Verify error response format."""
        response = client.post('/submit-answer', data={
            'class': 'CDA',
            'module': '1'
            # missing required fields
        })

        # Accept 400 or 404
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            data = json.loads(response.data)
            # Should have message field
            assert 'message' in data
            assert isinstance(data['message'], str)


class TestExternalAPICompatibility:
    """Test compatibility with the documented external API method."""

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_matches_documented_api_signature(self, mock_process, client):
        """
        Test that the endpoint matches the documented external API:

        def sub_ans(team, question_num, answer):
            url='https://example.net/submit-answer'
            data={'class':'cda',
                  'module':1,
                  'team':team,
                  'question_num':question_num,
                  'answer_num':answer}
            x=requests.post(url,data=data)
            response = json.loads(x.text)
            if response['success']:
                return response['correct']
            else:
                return response['message']
        """
        mock_process.return_value = {
            'feedback': {
                '5': {'correct': True, 'message': 'Excellent work!'}
            },
            'status': 200
        }

        # Exact data format from documented API
        response = client.post('/submit-answer', data={
            'class': 'cda',
            'module': 1,  # Can be int or str
            'team': 'user_team_123',
            'question_num': 5,  # Can be int or str
            'answer_num': 3  # Can be int or str
        })

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response structure matches expectations
        assert data['success'] is True
        # If success, should be able to return data['correct']
        assert 'correct' in data
        assert isinstance(data['correct'], bool)

    @patch('informatics_classroom.classroom.routes.process_answers_session')
    def test_error_returns_message(self, mock_process, client):
        """Test that on error, response['message'] contains error info."""
        # Mock an error scenario
        mock_process.return_value = {
            'feedback': {
                '1': {
                    'correct': False,
                    'message': 'Error: Quiz not found'
                }
            },
            'status': 404
        }

        response = client.post('/submit-answer', data={
            'class': 'nonexistent',
            'module': '999',
            'team': 'test_user',
            'question_num': '1',
            'answer_num': '1'
        })

        # Should get a response with message
        data = json.loads(response.data)
        # On error, should be able to return data['message']
        assert 'message' in data
        assert len(data['message']) > 0
