import random
import torch
from tensorboardX import SummaryWriter
from plotting_utils import plot_alignment_to_numpy, plot_spectrogram_to_numpy
from plotting_utils import plot_gate_outputs_to_numpy

#WAVEGLOW_MODEL_PATH = '/home/bt/models/waveglow-nvidia/waveglow_256channels_ljs_v2.pt'

#import sys
#sys.path.append('waveglow/') # Damn, the scary model loader tries to unpickle code and load local modules!

MELGAN_MODEL_PATH = '/home/bt/models/melgan-swpark/firstgo_a7c2351_6250.pt'

import sys
sys.path.append('/home/bt/dev/tacotron-melgan')
from model_melgan.generator import Generator

class Tacotron2Logger(SummaryWriter):
    def __init__(self, logdir, hparams):
        super(Tacotron2Logger, self).__init__(logdir)
        # NB(bt): If we omit the logdir, we get a nice default that segments by run
        #super(Tacotron2Logger, self).__init__()

        # Load waveglow and split the load between GPUs
        self.device = torch.device('cpu')
        #self.waveglow = torch.load(WAVEGLOW_MODEL_PATH, map_location=self.device)['model'].cpu()
        #self.waveglow.cuda().eval().half()
        #self.waveglow.eval().half()
        #self.waveglow.eval()
        #for k in self.waveglow.convinv:
        #    k.float()
        #with torch.cuda.device(self.device):
            #self.waveglow = torch.load(WAVEGLOW_MODEL_PATH)['model'].to(device)
        #    #self.waveglow = torch.load(WAVEGLOW_MODEL_PATH, map_location=gpu_index)['model']
        #    self.waveglow = torch.load(WAVEGLOW_MODEL_PATH)['model']
        self.sampling_rate = hparams.sampling_rate
        #self.melgan = Generator(self.hp.audio.n_mel_channels)
        checkpoint = torch.load(MELGAN_MODEL_PATH, map_location=torch.device('cpu'))
        self.melgan = Generator(80).cpu()
        self.melgan.load_state_dict(checkpoint['model_g'])
        self.melgan.eval(inference=False)

    def log_training(self, reduced_loss, grad_norm, learning_rate, duration,
                     iteration):
            self.add_scalar("training.loss", reduced_loss, iteration)
            self.add_scalar("grad.norm", grad_norm, iteration)
            self.add_scalar("learning.rate", learning_rate, iteration)
            self.add_scalar("duration", duration, iteration)

    def log_validation(self, reduced_loss, model, y, y_pred, iteration):
        self.add_scalar("validation.loss", reduced_loss, iteration)
        _, mel_outputs, gate_outputs, alignments = y_pred
        mel_targets, gate_targets = y

        # plot distribution of parameters
        for tag, value in model.named_parameters():
            tag = tag.replace('.', '/')
            self.add_histogram(tag, value.data.cpu().numpy(), iteration)

        # plot alignment, mel target and predicted, gate target and predicted
        idx = random.randint(0, alignments.size(0) - 1)
        self.add_image(
            "alignment",
            plot_alignment_to_numpy(alignments[idx].data.cpu().numpy().T),
            iteration, dataformats='HWC')
        self.add_image(
            "mel_target",
            plot_spectrogram_to_numpy(mel_targets[idx].data.cpu().numpy()),
            iteration, dataformats='HWC')
        self.add_image(
            "mel_predicted",
            plot_spectrogram_to_numpy(mel_outputs[idx].data.cpu().numpy()),
            iteration, dataformats='HWC')
        self.add_image(
            "gate",
            plot_gate_outputs_to_numpy(
                gate_targets[idx].data.cpu().numpy(),
                torch.sigmoid(gate_outputs[idx]).data.cpu().numpy()),
            iteration, dataformats='HWC')

        # Infer and log an audio sample
        #audio_tensor = None
        #with torch.cuda.device(self.device):
        #with torch.no_grad():
            #audio_tensor = self.waveglow.infer(mel_outputs[idx], sigma=0.666)
            #print(mel_outputs)
            #print(mel_outputs.device)
            #mel = mel_outputs.to(self.device)
            #print(mel)
            #print(mel.device)
        #audio_tensor = self.waveglow.infer(mel_outputs.to(self.device), sigma=0.666)
        #print(mel_outputs)
        #print(mel_outputs.device)
        #mel = mel_outputs.float().cpu().to(self.device)
        #print(mel)
        #print(mel.device)
        #print(mel.dtype)
        ##print(self.waveglow)
        #audio_tensor = self.waveglow.infer(mel, sigma=0.666)
        mel = mel_outputs.cpu()[0]
        print(mel)
        if len(mel.shape) == 2:
            mel = mel.unsqueeze(0)
            print(mel)
        audio = self.melgan.inference(mel)
        print(audio)

        print('>>>> SAVING AUDIO SAVING AUDIO')
        #torchaudio.save('amazing_sound.wav', audio.float().cpu(), hparams.sampling_rate)
        self.add_audio('audio',
                audio,
                global_step=iteration,
                sample_rate=self.sampling_rate,
                walltime=None)
        print('>>>> SAVED AUDIO')

