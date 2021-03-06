# Lint as: python2, python3
# Copyright 2020 The TensorFlow Probability Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the modelific language governing permissions and
# limitations under the License.
# ============================================================================
"""Tests for inference_gym.targets.item_response_theory."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import parameterized
import numpy as np
import tensorflow.compat.v2 as tf

from tensorflow_probability.python.experimental.inference_gym.internal import test_util
from tensorflow_probability.python.experimental.inference_gym.targets import item_response_theory
from tensorflow_probability.python.internal import test_util as tfp_test_util


def _test_dataset(num_test_pairs=None):
  return dict(
      train_student_ids=np.arange(20),
      train_question_ids=(np.arange(20) % 10),
      train_correct=np.arange(20) % 2,
      test_student_ids=(np.arange(num_test_pairs) if num_test_pairs else None),
      test_question_ids=(np.arange(num_test_pairs) %
                         10 if num_test_pairs else None),
      test_correct=(np.arange(num_test_pairs) % 2 if num_test_pairs else None),
  )


class ItemResponseTheoryTest(test_util.InferenceGymTestCase,
                             parameterized.TestCase):

  @tfp_test_util.numpy_disable_test_missing_functionality(
      'tf.gather_nd and batch_dims > 0')
  @parameterized.named_parameters(
      ('NoTest', None),
      ('WithTest', 5),
  )
  def testBasic(self, num_test_points):
    """Checks that you get finite values given unconstrained samples.

    We check `unnormalized_log_prob` as well as the values of the sample
    transformations.

    Args:
      num_test_points: Number of test points.
    """
    model = item_response_theory.ItemResponseTheory(
        **_test_dataset(num_test_points))
    self.validate_log_prob_and_transforms(
        model,
        sample_transformation_shapes=dict(
            identity={
                'mean_student_ability': [],
                'student_ability': [20],
                'question_difficulty': [10],
            },
            test_nll=[],
            per_example_test_nll=[num_test_points],
        ))

  def testPartiallySpecifiedTestSet(self):
    """Check that partially specified test set raises an error."""
    num_test_points = 5
    dataset = _test_dataset(num_test_points)
    del dataset['test_student_ids']
    with self.assertRaisesRegex(ValueError, 'all be specified'):
      item_response_theory.ItemResponseTheory(**dataset)

  def testSyntheticItemResponseTheory(self):
    """Checks that you get finite values given unconstrained samples.

    We check `unnormalized_log_prob` as well as the values of the sample
    transformations.
    """
    model = item_response_theory.SyntheticItemResponseTheory()
    self.validate_log_prob_and_transforms(
        model,
        sample_transformation_shapes=dict(
            identity={
                'mean_student_ability': [],
                'student_ability': [400],
                'question_difficulty': [100],
            },),
        check_ground_truth_mean_standard_error=True,
        check_ground_truth_mean=True,
        check_ground_truth_standard_deviation=True,
    )

  @tfp_test_util.numpy_disable_gradient_test
  @tfp_test_util.jax_disable_test_missing_functionality('tfp.mcmc')
  def testSyntheticItemResponseTheoryHMC(self):
    """Checks approximate samples from the model against the ground truth."""
    # Note the side-effect of setting the eager seed.
    seed = tfp_test_util.test_seed_stream()
    model = item_response_theory.SyntheticItemResponseTheory()

    self.validate_ground_truth_using_hmc(
        model,
        num_chains=4,
        num_steps=5000,
        num_leapfrog_steps=10,
        step_size=0.025,
        seed=seed(),
    )


if __name__ == '__main__':
  tf.test.main()
