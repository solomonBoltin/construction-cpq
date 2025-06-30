import { useQuoteBuilderStore } from '../stores/useQuoteBuilderStore';
import { STEPS } from '../config/quoteBuilder';
import { ProductRole } from '../types';

export const useStepNavigation = () => {
  const { activeStep, setStep, quote, selectedCategoryName } = useQuoteBuilderStore();
  const currentIndex = STEPS.findIndex(s => s.key === activeStep);
  const currentStep = STEPS[currentIndex];
  
  // Get fresh state from store instead of using closure values
  const getFreshState = () => useQuoteBuilderStore.getState();
  
  // Check if current step allows proceeding to next
  const canGoNext = () => {
    const { quote, selectedCategoryName } = getFreshState();
    if (!currentStep?.canProceed) return true;
    return currentStep.canProceed(quote, selectedCategoryName);
  };
  
  const canGoPrev = () => {
    return currentIndex > 0;
  };

  // Determine if a step is accessible (can be clicked)
  const isStepAccessible = (stepIndex: number): boolean => {
    const { quote, selectedCategoryName, activeStep } = getFreshState();
    const currentIdx = STEPS.findIndex(s => s.key === activeStep);
    
    // Current step is always accessible
    if (stepIndex === currentIdx) return true;
    
    // Can always go back to previous steps
    if (stepIndex < currentIdx) return true;
    
    // For forward navigation, check if all previous steps can proceed
    for (let i = 0; i < stepIndex; i++) {
      const step = STEPS[i];
      if (step.canProceed && !step.canProceed(quote, selectedCategoryName)) {
        return false;
      }
    }
    return true;
  };

  // Get the status of a step
  const getStepStatus = (stepIndex: number): 'active' | 'completed' | 'enabled' | 'disabled' => {
    const step = STEPS[stepIndex];
    
    // Current step is active
    if (stepIndex === currentIndex) return 'active';
    
    // Check if step is completed
    if (step.isCompleted && step.isCompleted(quote, selectedCategoryName)) {
      return 'completed';
    }
    
    // Check if step is accessible
    if (isStepAccessible(stepIndex)) {
      return 'enabled';
    }
    
    return 'disabled';
  };

  const goNext = () => {
    if (currentIndex < STEPS.length - 1 && canGoNext()) {
      setStep(STEPS[currentIndex + 1].key);
    }
  };
  
  const goPrev = () => {
    if (canGoPrev()) {
      setStep(STEPS[currentIndex - 1].key);
    }
  };
  
  const goToStep = (stepKey: string) => {
    const targetIndex = STEPS.findIndex(s => s.key === stepKey);
    if (targetIndex !== -1 && isStepAccessible(targetIndex)) {
      setStep(STEPS[targetIndex].key);
    } else {
      console.warn(`Step "${stepKey}" is not accessible or does not exist.`);
    }
  };

  // Navigate to the appropriate step after an action
  const navigateAfterAction = (action: 'categorySelected' | 'productSelected', role?: ProductRole) => {
    switch (action) {
      case 'categorySelected':
        goToStep('choose_main_product');
        break;
      case 'productSelected':
        if (role === ProductRole.MAIN) {
          goToStep('configure_main');
        } else if (role === ProductRole.SECONDARY) {
          goToStep('configure_secondary');
        }
        break;
    }
  };

  // Find the next incomplete step (useful for smart navigation)
  const getNextIncompleteStep = (): string | null => {
    const { quote, selectedCategoryName } = getFreshState();
    for (let i = 0; i < STEPS.length; i++) {
      const step = STEPS[i];
      if (step.isCompleted && !step.isCompleted(quote, selectedCategoryName)) {
        return step.key;
      }
    }
    return null;
  };

  return {
    currentStep: currentStep?.key || 'choose_category',
    currentIndex,
    totalSteps: STEPS.length,
    canGoNext: canGoNext(),
    canGoPrev: canGoPrev(),
    canAccessStep: isStepAccessible,
    goNext,
    goPrev,
    goToStep,
    getStepStatus,
    navigateAfterAction,
    getNextIncompleteStep,
  };
};
