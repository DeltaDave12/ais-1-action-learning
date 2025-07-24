import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import matplotlib.pyplot as plt
import time
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from improved_emotion_recognition import (
    ImprovedEmotionRecognitionModel, 
    ImprovedTransformerEmotionModel, 
    CustomDataset,
    device
)

class ProgressiveEmotionTrainer:
    def __init__(self):
        self.model = ImprovedEmotionRecognitionModel()
        self.training_history = {
            'stage1': {'train_losses': [], 'val_losses': [], 'train_accs': [], 'val_accs': []},
            'stage2': {'train_losses': [], 'val_losses': [], 'train_accs': [], 'val_accs': []}
        }
        
    def load_datasets(self):
        """Load both clean and noisy datasets"""
        print("="*60)
        print("LOADING DATASETS")
        print("="*60)
        
        # Load clean dataset
        print("\n1. Loading clean dataset...")
        self.clean_df = pd.read_csv("../data/datasets/student_emotion_dataset_80k_balanced.csv")
        print(f"   Clean dataset: {len(self.clean_df)} samples")
        print(f"   Emotion distribution:")
        print(self.clean_df['emotion'].value_counts(normalize=True).round(3))
        
        # Load noisy dataset
        print("\n2. Loading noisy dataset...")
        self.noisy_df = pd.read_csv("../data/datasets/student_emotion_dataset_80k_noisy.csv")
        print(f"   Noisy dataset: {len(self.noisy_df)} samples")
        print(f"   Emotion distribution:")
        print(self.noisy_df['emotion'].value_counts(normalize=True).round(3))
        
        # Load test dataset
        print("\n3. Loading test dataset...")
        self.test_df = pd.read_csv("../data/datasets/student_emotion_dataset_test_20k_balanced.csv")
        print(f"   Test dataset: {len(self.test_df)} samples")
        
        return True
    
    def prepare_stage1_data(self):
        """Prepare data for Stage 1: Training on clean data"""
        print("\n" + "="*60)
        print("STAGE 1: PREPARING CLEAN DATA")
        print("="*60)
        
        # Prepare features from clean data
        X_clean = self.model.enhanced_feature_preparation(self.clean_df, fit_vectorizer=True, augment=False)
        y_clean = self.model.label_encoder.fit_transform(self.clean_df['emotion'])
        
        # Split clean data into train/validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_clean, y_clean, 
            test_size=0.2, 
            random_state=42, 
            stratify=y_clean
        )
        
        # Create datasets
        self.stage1_train_dataset = CustomDataset(
            torch.FloatTensor(X_train),
            torch.LongTensor(y_train)
        )
        self.stage1_val_dataset = CustomDataset(
            torch.FloatTensor(X_val),
            torch.LongTensor(y_val)
        )
        
        # Create dataloaders
        self.stage1_train_loader = DataLoader(
            self.stage1_train_dataset,
            batch_size=64,
            shuffle=True,
            num_workers=0,
            pin_memory=True,
            generator=torch.Generator(device=device)
        )
        self.stage1_val_loader = DataLoader(
            self.stage1_val_dataset,
            batch_size=64,
            shuffle=False,
            num_workers=0,
            pin_memory=True
        )
        
        print(f"Stage 1 data prepared:")
        print(f"  Training samples: {len(self.stage1_train_dataset)}")
        print(f"  Validation samples: {len(self.stage1_val_dataset)}")
        print(f"  Feature dimensions: {X_clean.shape[1]}")
        
        return X_clean.shape[1]
    
    def prepare_stage2_data(self):
        """Prepare data for Stage 2: Fine-tuning on noisy data"""
        print("\n" + "="*60)
        print("STAGE 2: PREPARING NOISY DATA")
        print("="*60)
        
        # Prepare features from noisy data (using same vectorizers)
        X_noisy = self.model.enhanced_feature_preparation(self.noisy_df, fit_vectorizer=False, augment=False)
        y_noisy = self.model.label_encoder.transform(self.noisy_df['emotion'])
        
        # Split noisy data into train/validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_noisy, y_noisy,
            test_size=0.2,
            random_state=42,
            stratify=y_noisy
        )
        
        # Create datasets
        self.stage2_train_dataset = CustomDataset(
            torch.FloatTensor(X_train),
            torch.LongTensor(y_train)
        )
        self.stage2_val_dataset = CustomDataset(
            torch.FloatTensor(X_val),
            torch.LongTensor(y_val)
        )
        
        # Create dataloaders
        self.stage2_train_loader = DataLoader(
            self.stage2_train_dataset,
            batch_size=64,
            shuffle=True,
            num_workers=0,
            pin_memory=True,
            generator=torch.Generator(device=device)
        )
        self.stage2_val_loader = DataLoader(
            self.stage2_val_dataset,
            batch_size=64,
            shuffle=False,
            num_workers=0,
            pin_memory=True
        )
        
        print(f"Stage 2 data prepared:")
        print(f"  Training samples: {len(self.stage2_train_dataset)}")
        print(f"  Validation samples: {len(self.stage2_val_dataset)}")
        
        return X_noisy.shape[1]
    
    def prepare_test_data(self):
        """Prepare test data for final evaluation"""
        print("\n" + "="*60)
        print("PREPARING TEST DATA")
        print("="*60)
        
        # Prepare features from test data
        X_test = self.model.enhanced_feature_preparation(self.test_df, fit_vectorizer=False, augment=False)
        y_test = self.model.label_encoder.transform(self.test_df['emotion'])
        
        # Create test dataset and loader
        self.test_dataset = CustomDataset(
            torch.FloatTensor(X_test),
            torch.LongTensor(y_test)
        )
        self.test_loader = DataLoader(
            self.test_dataset,
            batch_size=64,
            shuffle=False,
            num_workers=0,
            pin_memory=True
        )
        
        print(f"Test data prepared: {len(self.test_dataset)} samples")
        return X_test.shape[1]
    
    def train_stage1(self, feature_size):
        """Stage 1: Train on clean data"""
        print("\n" + "="*60)
        print("STAGE 1: TRAINING ON CLEAN DATA")
        print("="*60)
        
        # Initialize model
        self.model.model = ImprovedTransformerEmotionModel(
            text_feature_size=feature_size,
            num_classes=len(self.model.label_encoder.classes_),
            d_model=512,
            nhead=8,
            num_layers=4,
            dropout=0.2
        ).to(device)
        
        # Print model summary
        total_params = sum(p.numel() for p in self.model.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.model.parameters() if p.requires_grad)
        print(f"Model Summary:")
        print(f"  Total parameters: {total_params:,}")
        print(f"  Trainable parameters: {trainable_params:,}")
        
        # Training setup
        criterion, optimizer, scheduler = self.model.advanced_training_setup(self.model.model, learning_rate=0.0001)
        
        # Training loop
        best_val_acc = 0
        patience = 15
        patience_counter = 0
        
        print("\nStarting Stage 1 training...")
        epoch_pbar = tqdm(range(50), desc='Stage 1 Training')
        
        for epoch in epoch_pbar:
            # Training
            self.model.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            for text_batch, labels in self.stage1_train_loader:
                text_batch = text_batch.to(device)
                labels = labels.to(device)
                
                optimizer.zero_grad()
                outputs = self.model.model(text_batch)
                loss = criterion(outputs, labels)
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.model.parameters(), max_norm=1.0)
                
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()
            
            train_loss = train_loss / len(self.stage1_train_loader)
            train_acc = train_correct / train_total
            
            # Validation
            self.model.model.eval()
            val_loss = 0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for text_batch, labels in self.stage1_val_loader:
                    text_batch = text_batch.to(device)
                    labels = labels.to(device)
                    
                    outputs = self.model.model(text_batch)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()
            
            val_loss = val_loss / len(self.stage1_val_loader)
            val_acc = val_correct / val_total
            
            # Update learning rate
            scheduler.step()
            
            # Store history
            self.training_history['stage1']['train_losses'].append(train_loss)
            self.training_history['stage1']['val_losses'].append(val_loss)
            self.training_history['stage1']['train_accs'].append(train_acc)
            self.training_history['stage1']['val_accs'].append(val_acc)
            
            # Update progress bar
            epoch_pbar.set_postfix({
                'train_loss': f'{train_loss:.4f}',
                'train_acc': f'{train_acc:.4f}',
                'val_loss': f'{val_loss:.4f}',
                'val_acc': f'{val_acc:.4f}',
                'lr': f'{scheduler.get_last_lr()[0]:.6f}'
            })
            
            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                # Save Stage 1 model
                torch.save({
                    'model_state_dict': self.model.model.state_dict(),
                    'stage': 'stage1',
                    'history': self.training_history['stage1'],
                    'vectorizers': {
                        'tfidf': self.model.tfidf_vectorizer,
                        'count': self.model.count_vectorizer
                    },
                    'label_encoder': self.model.label_encoder
                }, 'progressive_model_stage1.pth')
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                print(f"\nStage 1 early stopping at epoch {epoch}")
                break
        
        print(f"\nStage 1 completed!")
        print(f"Best validation accuracy: {best_val_acc:.4f}")
        return best_val_acc
    
    def train_stage2(self, feature_size):
        """Stage 2: Fine-tune on noisy data"""
        print("\n" + "="*60)
        print("STAGE 2: FINE-TUNING ON NOISY DATA")
        print("="*60)
        
        # Load Stage 1 model
        checkpoint = torch.load('progressive_model_stage1.pth')
        self.model.model.load_state_dict(checkpoint['model_state_dict'])
        print("Loaded Stage 1 model weights")
        
        # Training setup with lower learning rate for fine-tuning
        criterion, optimizer, scheduler = self.model.advanced_training_setup(self.model.model, learning_rate=0.00001)
        
        # Training loop
        best_val_acc = 0
        patience = 10
        patience_counter = 0
        
        print("\nStarting Stage 2 fine-tuning...")
        epoch_pbar = tqdm(range(30), desc='Stage 2 Fine-tuning')
        
        for epoch in epoch_pbar:
            # Training
            self.model.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            for text_batch, labels in self.stage2_train_loader:
                text_batch = text_batch.to(device)
                labels = labels.to(device)
                
                optimizer.zero_grad()
                outputs = self.model.model(text_batch)
                loss = criterion(outputs, labels)
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.model.parameters(), max_norm=0.5)
                
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()
            
            train_loss = train_loss / len(self.stage2_train_loader)
            train_acc = train_correct / train_total
            
            # Validation
            self.model.model.eval()
            val_loss = 0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for text_batch, labels in self.stage2_val_loader:
                    text_batch = text_batch.to(device)
                    labels = labels.to(device)
                    
                    outputs = self.model.model(text_batch)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()
            
            val_loss = val_loss / len(self.stage2_val_loader)
            val_acc = val_correct / val_total
            
            # Update learning rate
            scheduler.step()
            
            # Store history
            self.training_history['stage2']['train_losses'].append(train_loss)
            self.training_history['stage2']['val_losses'].append(val_loss)
            self.training_history['stage2']['train_accs'].append(train_acc)
            self.training_history['stage2']['val_accs'].append(val_acc)
            
            # Update progress bar
            epoch_pbar.set_postfix({
                'train_loss': f'{train_loss:.4f}',
                'train_acc': f'{train_acc:.4f}',
                'val_loss': f'{val_loss:.4f}',
                'val_acc': f'{val_acc:.4f}',
                'lr': f'{scheduler.get_last_lr()[0]:.6f}'
            })
            
            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                # Save Stage 2 model
                torch.save({
                    'model_state_dict': self.model.model.state_dict(),
                    'stage': 'stage2',
                    'history': self.training_history,
                    'vectorizers': {
                        'tfidf': self.model.tfidf_vectorizer,
                        'count': self.model.count_vectorizer
                    },
                    'label_encoder': self.model.label_encoder
                }, 'progressive_model_stage2.pth')
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                print(f"\nStage 2 early stopping at epoch {epoch}")
                break
        
        print(f"\nStage 2 completed!")
        print(f"Best validation accuracy: {best_val_acc:.4f}")
        return best_val_acc
    
    def evaluate_final_model(self):
        """Evaluate the final model on test data"""
        print("\n" + "="*60)
        print("FINAL EVALUATION ON TEST DATA")
        print("="*60)
        
        # Load final model
        checkpoint = torch.load('progressive_model_stage2.pth')
        self.model.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.model.eval()
        
        # Comprehensive evaluation
        evaluation = self.model.comprehensive_evaluation(self.model.model, self.test_loader, device)
        
        print(f"\nFinal Test Results:")
        print(f"  Accuracy: {evaluation['accuracy']:.4f}")
        print(f"  Macro F1: {evaluation['macro_f1']:.4f}")
        print(f"  Weighted F1: {evaluation['weighted_f1']:.4f}")
        print(f"  Mean ROC-AUC: {evaluation['mean_roc_auc']:.4f}")
        
        # Per-class ROC-AUC
        print(f"\nPer-class ROC-AUC:")
        for i, emotion in enumerate(self.model.label_encoder.classes_):
            print(f"  {emotion}: {evaluation['roc_auc_scores'][i]:.4f}")
        
        # Save evaluation results
        torch.save(evaluation, 'progressive_evaluation_results.pth')
        
        return evaluation
    
    def plot_training_progress(self):
        """Plot training progress for both stages"""
        if not hasattr(self, 'training_history'):
            return
        
        plt.figure(figsize=(15, 10))
        
        # Stage 1 plots
        plt.subplot(2, 3, 1)
        plt.plot(self.training_history['stage1']['train_losses'], label='Train Loss', linewidth=2)
        plt.plot(self.training_history['stage1']['val_losses'], label='Val Loss', linewidth=2)
        plt.title('Stage 1: Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 3, 2)
        plt.plot(self.training_history['stage1']['train_accs'], label='Train Acc', linewidth=2)
        plt.plot(self.training_history['stage1']['val_accs'], label='Val Acc', linewidth=2)
        plt.title('Stage 1: Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Stage 2 plots
        plt.subplot(2, 3, 4)
        plt.plot(self.training_history['stage2']['train_losses'], label='Train Loss', linewidth=2)
        plt.plot(self.training_history['stage2']['val_losses'], label='Val Loss', linewidth=2)
        plt.title('Stage 2: Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 3, 5)
        plt.plot(self.training_history['stage2']['train_accs'], label='Train Acc', linewidth=2)
        plt.plot(self.training_history['stage2']['val_accs'], label='Val Acc', linewidth=2)
        plt.title('Stage 2: Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Combined accuracy comparison
        plt.subplot(2, 3, 3)
        plt.plot(self.training_history['stage1']['val_accs'], label='Stage 1 Val', linewidth=2)
        plt.plot(self.training_history['stage2']['val_accs'], label='Stage 2 Val', linewidth=2)
        plt.title('Validation Accuracy Comparison')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Combined loss comparison
        plt.subplot(2, 3, 6)
        plt.plot(self.training_history['stage1']['val_losses'], label='Stage 1 Val', linewidth=2)
        plt.plot(self.training_history['stage2']['val_losses'], label='Stage 2 Val', linewidth=2)
        plt.title('Validation Loss Comparison')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('progressive_training_progress.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Training progress plots saved as 'progressive_training_progress.png'")
    
    def run_progressive_training(self):
        """Run the complete progressive training pipeline"""
        print("="*80)
        print("PROGRESSIVE EMOTION RECOGNITION TRAINING")
        print("="*80)
        print("\nStrategy: Train on clean data first, then fine-tune on noisy data")
        print("This approach helps the model learn robust features before handling noise.")
        
        # Load datasets
        self.load_datasets()
        
        # Prepare data for all stages
        feature_size = self.prepare_stage1_data()
        self.prepare_stage2_data()
        self.prepare_test_data()
        
        # Stage 1: Train on clean data
        stage1_best_acc = self.train_stage1(feature_size)
        
        # Stage 2: Fine-tune on noisy data
        stage2_best_acc = self.train_stage2(feature_size)
        
        # Final evaluation
        final_results = self.evaluate_final_model()
        
        # Plot training progress
        self.plot_training_progress()
        
        # Summary
        print("\n" + "="*80)
        print("PROGRESSIVE TRAINING COMPLETED!")
        print("="*80)
        print(f"\nStage 1 (Clean Data) Best Accuracy: {stage1_best_acc:.4f}")
        print(f"Stage 2 (Noisy Data) Best Accuracy: {stage2_best_acc:.4f}")
        print(f"Final Test Accuracy: {final_results['accuracy']:.4f}")
        print(f"Final Test Macro F1: {final_results['macro_f1']:.4f}")
        print(f"Final Test ROC-AUC: {final_results['mean_roc_auc']:.4f}")
        
        print(f"\nFiles generated:")
        print("✓ progressive_model_stage1.pth (clean data model)")
        print("✓ progressive_model_stage2.pth (final model)")
        print("✓ progressive_evaluation_results.pth (test results)")
        print("✓ progressive_training_progress.png (training plots)")
        
        print(f"\nBenefits of progressive training:")
        print("✓ Model learns robust features from clean data first")
        print("✓ Fine-tuning adapts to noise without forgetting clean patterns")
        print("✓ Better generalization to real-world noisy scenarios")
        print("✓ Improved robustness to typos, synonyms, and label noise")
        
        return final_results

def main():
    # Set random seed
    current_time = int(time.time())
    torch.manual_seed(current_time)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(current_time)
        torch.cuda.manual_seed_all(current_time)
    np.random.seed(current_time)
    
    # Initialize trainer and run progressive training
    trainer = ProgressiveEmotionTrainer()
    results = trainer.run_progressive_training()
    
    return results

if __name__ == "__main__":
    main() 