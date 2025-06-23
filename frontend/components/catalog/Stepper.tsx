
import React from 'react';
import { useQuoteProcess } from '../../contexts/QuoteProcessContext';
import { Steps } from '../../constants';
import CheckIcon from '../icons/CheckIcon';

const Stepper: React.FC = () => {
    const { activeStep, goToStep } = useQuoteProcess();
    const currentIndex = Steps.findIndex(s => s.key === activeStep);

    return (
        <nav aria-label="Progress">
            <ol role="list" className="flex items-center space-x-2 sm:space-x-4 text-xs sm:text-sm font-medium text-slate-500 overflow-x-auto pb-2">
                {Steps.map((step, index) => {
                    const isCompleted = index < currentIndex;
                    const isCurrent = index === currentIndex;
                    
                    let icon;
                    let textClass = 'text-slate-400';
                    let statusClass = 'border-slate-300 bg-white text-slate-400';

                    if (isCurrent) {
                        textClass = 'text-blue-600 font-bold';
                        statusClass = 'bg-blue-600 text-white';
                    } else if (isCompleted) {
                        textClass = 'text-green-600 hover:text-green-800';
                        statusClass = 'bg-green-500 text-white';
                    }

                    icon = (
                        <span className={`flex h-6 w-6 items-center justify-center rounded-full border ${statusClass} mr-2 text-xs`}>
                            {isCompleted ? <CheckIcon className="h-4 w-4" /> : index + 1}
                        </span>
                    );
                    
                    return (
                        <li key={step.key} className={`flex items-center ${index > 0 ? 'pl-2 sm:pl-4' : ''} relative whitespace-nowrap`}>
                            {index > 0 && <div className="absolute -left-1 sm:-left-2 top-1/2 h-0.5 w-3 sm:w-4 bg-slate-200 transform -translate-y-1/2" />}
                            <button 
                                onClick={() => goToStep(step.key)} 
                                className={`flex items-center ${textClass} ${!isCurrent && !isCompleted ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
                                disabled={!isCurrent && !isCompleted && !isCompleted} // Allow going back to completed steps
                                aria-current={isCurrent ? 'step' : undefined}
                            >
                                {icon}
                                {step.label}
                            </button>
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
};

export default Stepper;
