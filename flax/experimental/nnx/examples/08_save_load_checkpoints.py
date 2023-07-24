# Copyright 2023 The Flax Authors.
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
# See the License for the specific language governing permissions and
# limitations under the License.

from tempfile import TemporaryDirectory

import jax
import jax.numpy as jnp
import orbax.checkpoint as orbax

from flax.experimental import nnx


class MLP(nnx.Module):

  def __init__(self, din: int, dmid: int, dout: int, *, ctx: nnx.Context):
    self.dense1 = nnx.Linear(din, dmid, ctx=ctx)
    self.dense2 = nnx.Linear(dmid, dout, ctx=ctx)

  def __call__(self, x: jax.Array) -> jax.Array:
    x = self.dense1(x)
    x = jax.nn.relu(x)
    x = self.dense2(x)
    return x


def create_model(seed: int):
  return MLP(10, 20, 30, ctx=nnx.context(seed))


def create_and_save(seed: int, path: str):
  model = create_model(seed)
  state = model.get_state()
  # Save the parameters
  checkpointer = orbax.PyTreeCheckpointer()
  checkpointer.save(f"{path}/state", state)


def load_model(path: str) -> MLP:
  # create that model with abstract shapes
  state, moduledef = jax.eval_shape(lambda: create_model(0).partition())
  # Load the parameters
  checkpointer = orbax.PyTreeCheckpointer()
  state = checkpointer.restore(f"{path}/state", item=state)
  # Merge the parameters into the model
  model = moduledef.merge(state)
  return model


with TemporaryDirectory() as tmpdir:
  # create a checkpoint
  create_and_save(42, tmpdir)
  # load model from checkpoint
  model = load_model(tmpdir)
  # run the model
  y = model(jnp.ones((1, 10)))
  print(model)
  print(y)
