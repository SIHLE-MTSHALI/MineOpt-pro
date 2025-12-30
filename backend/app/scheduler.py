from typing import List, Dict, Optional
from backend.app.models import Block, QualitySpecs

class BlockScheduler:
    def __init__(self):
        self.blocks: Dict[str, Block] = {}
        
    def add_block(self, block: Block):
        """Add a block to the model and update its status based on dependencies."""
        self.blocks[block.block_id] = block
        self.update_block_status(block.block_id)

    def update_block_status(self, block_id: str):
        """Check dependencies and update status."""
        block = self.blocks.get(block_id)
        if not block or block.status == 'mined':
            return

        # Check if all dependencies are mined
        all_deps_mined = True
        for dep_id in block.dependencies:
            dep = self.blocks.get(dep_id)
            if not dep or dep.status != 'mined':
                all_deps_mined = False
                break
        
        if all_deps_mined:
            if block.status == 'blocked':
                block.status = 'available'
        else:
            block.status = 'blocked'

    def mine_block(self, block_id: str, amount: float) -> Optional[QualitySpecs]:
        """
        Mine 'amount' tonnes from the block.
        Returns the quality of the mined material.
        Updates status to 'mined' if depleted.
        """
        block = self.blocks.get(block_id)
        if not block or block.status not in ['available', 'mining']:
            return None
        
        block.status = 'mining'
        
        # Determine actual amount mined (cap at remaining)
        mined_amount = min(amount, block.tonnes)
        block.tonnes -= mined_amount
        
        if block.tonnes <= 0:
            block.tonnes = 0
            block.status = 'mined'
            # Trigger update for any blocks dependent on this one
            self.refresh_dependencies()
            
        return block.quality

    def refresh_dependencies(self):
        """Re-scan all blocks to unlock those whose dependencies are now met."""
        for b_id in self.blocks:
            self.update_block_status(b_id)

    def get_available_blocks(self) -> List[Block]:
        return [b for b in self.blocks.values() if b.status in ['available', 'mining']]

    def get_all_blocks(self) -> List[Block]:
        return list(self.blocks.values())

    def reset(self):
        self.blocks = {}
