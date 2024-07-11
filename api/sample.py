import os
import pickle
from contextlib import nullcontext
import torch
import tiktoken
from model import GPTConfig, GPT

class GPTSampler:
    def __init__(self, init_from='resume', out_dir='out-shakespeare', num_samples=1, 
                 max_new_tokens=200, temperature=0.8, top_k=5, seed=1337, device='cpu', compile=False):
        self.init_from = init_from
        self.out_dir = out_dir
        self.num_samples = num_samples
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_k = top_k
        self.seed = seed
        self.device = device
        self.compile = compile

        self.device_type = 'cuda' if 'cuda' in self.device else 'cpu'
        self.dtype = 'bfloat16' if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else 'float16'
        self.ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[self.dtype]
        self.ctx = nullcontext() if self.device_type == 'cpu' else torch.amp.autocast(device_type=self.device_type, dtype=self.ptdtype)

        self._set_seed()
        self.model = self._load_model()
        self.encode, self.decode = self._get_encoder_decoder()

    def _set_seed(self):
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed(self.seed)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    def _load_model(self):
        if self.init_from == 'resume':
            ckpt_path = os.path.join(self.out_dir, 'ckpt.pt')
            checkpoint = torch.load(ckpt_path, map_location=self.device)
            gptconf = GPTConfig(**checkpoint['model_args'])
            model = GPT(gptconf)
            state_dict = checkpoint['model']
            unwanted_prefix = '_orig_mod.'
            for k, v in list(state_dict.items()):
                if k.startswith(unwanted_prefix):
                    state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
            model.load_state_dict(state_dict)
        elif self.init_from.startswith('gpt2'):
            model = GPT.from_pretrained(self.init_from, dict(dropout=0.0))

        model.eval()
        model.to(self.device)
        if self.compile:
            model = torch.compile(model)  # requires PyTorch 2.0 (optional)
        return model

    def _get_encoder_decoder(self):
        load_meta = False
        if self.init_from == 'resume':
            ckpt_path = os.path.join(self.out_dir, 'ckpt.pt')
            checkpoint = torch.load(ckpt_path, map_location=self.device)
            if 'config' in checkpoint and 'dataset' in checkpoint['config']:
                meta_path = os.path.join('data', checkpoint['config']['dataset'], 'meta.pkl')
                load_meta = os.path.exists(meta_path)
        if load_meta:
            with open(meta_path, 'rb') as f:
                meta = pickle.load(f)
            stoi, itos = meta['stoi'], meta['itos']
            encode = lambda s: [stoi[c] for c in s]
            decode = lambda l: ''.join([itos[i] for i in l])
        else:
            enc = tiktoken.get_encoding("gpt2")
            encode = lambda s: enc.encode(s, allowed_special={""})
            decode = lambda l: enc.decode(l)
        return encode, decode

    def generate_samples(self, start):
        start_ids = self.encode(start)
        x = torch.tensor(start_ids, dtype=torch.long, device=self.device)[None, ...]

        generated_texts = []

        with torch.no_grad():
            with self.ctx:
                for k in range(self.num_samples):
                    y = self.model.generate(x, self.max_new_tokens, temperature=self.temperature, top_k=self.top_k)
                    generated_text = self.decode(y[0].tolist())
                    generated_texts.append(generated_text)

        return generated_texts

